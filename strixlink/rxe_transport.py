"""RDMA (soft-RoCE / rxe) transport for strixlink.

Real one-sided RDMA over the Thunderbolt link using the in-kernel rxe device.
RDMA WRITE/READ touch the peer's registered memory directly, without the peer
CPU participating per-op. A tiny side-channel exchanges the QP bootstrap
(qpn/psn/gid) and the remote region's addr+rkey; after that data moves over
verbs.

Requires an rxe device bound to the link:
    sudo rdma link add rxe_tb type rxe netdev thunderbolt0
"""
from __future__ import annotations

import json
import socket

from pyverbs.cq import CQ
from pyverbs.device import Context
from pyverbs.pd import PD
from pyverbs.mr import MR
from pyverbs.qp import QP, QPCap, QPInitAttr, QPAttr
from pyverbs.addr import AHAttr, GlobalRoute, GID
from pyverbs.wr import SGE, SendWR
from pyverbs import libibverbs_enums as e

QPS = e.ibv_qp_state
ACC = e.ibv_access_flags
MASK = e.ibv_qp_attr_mask
OP = e.ibv_wr_opcode
MTU = e.ibv_mtu
QPT = e.ibv_qp_type
WC = e.ibv_wc_status


class RxeEndpoint:
    """One RC queue pair between two rxe devices. Each side registers a region,
    they exchange (addr, rkey, qpn, gid), connect, then either side can
    rdma_write / rdma_read into the other's region."""

    def __init__(self, dev: str = "rxe_tb", region_size: int = 1 << 20):
        self.ctx = Context(name=dev)
        self.pd = PD(self.ctx)
        self.cq = CQ(self.ctx, 16)
        self.region_size = region_size
        access = ACC.IBV_ACCESS_LOCAL_WRITE | ACC.IBV_ACCESS_REMOTE_WRITE | ACC.IBV_ACCESS_REMOTE_READ
        self.mr = MR(self.pd, region_size, access)
        cap = QPCap(max_send_wr=16, max_recv_wr=16, max_send_sge=1, max_recv_sge=1)
        init = QPInitAttr(qp_type=QPT.IBV_QPT_RC, scq=self.cq, rcq=self.cq, cap=cap)
        self.qp = QP(self.pd, init)
        self.gid = self.ctx.query_gid(1, 0)
        self.port_attr = self.ctx.query_port(1)

    def local_conn(self) -> dict:
        return {"qpn": self.qp.qp_num, "psn": 0, "gid": str(self.gid),
                "addr": self.mr.buf, "rkey": self.mr.rkey}

    def connect(self, remote: dict):
        a = QPAttr()
        a.qp_state = QPS.IBV_QPS_INIT
        a.pkey_index = 0
        a.port_num = 1
        a.qp_access_flags = ACC.IBV_ACCESS_REMOTE_WRITE | ACC.IBV_ACCESS_REMOTE_READ
        self.qp.modify(a, MASK.IBV_QP_STATE | MASK.IBV_QP_PKEY_INDEX | MASK.IBV_QP_PORT | MASK.IBV_QP_ACCESS_FLAGS)

        a = QPAttr()
        a.qp_state = QPS.IBV_QPS_RTR
        a.path_mtu = MTU.IBV_MTU_1024
        a.dest_qp_num = remote["qpn"]
        a.rq_psn = remote["psn"]
        a.max_dest_rd_atomic = 1
        a.min_rnr_timer = 12
        gr = GlobalRoute(dgid=GID(remote["gid"]), sgid_index=0, hop_limit=1)
        a.ah_attr = AHAttr(gr=gr, is_global=1, port_num=1)
        self.qp.modify(a, MASK.IBV_QP_STATE | MASK.IBV_QP_AV | MASK.IBV_QP_PATH_MTU |
                       MASK.IBV_QP_DEST_QPN | MASK.IBV_QP_RQ_PSN |
                       MASK.IBV_QP_MAX_DEST_RD_ATOMIC | MASK.IBV_QP_MIN_RNR_TIMER)

        a = QPAttr()
        a.qp_state = QPS.IBV_QPS_RTS
        a.timeout = 14
        a.retry_cnt = 7
        a.rnr_retry = 7
        a.sq_psn = 0
        a.max_rd_atomic = 1
        self.qp.modify(a, MASK.IBV_QP_STATE | MASK.IBV_QP_TIMEOUT | MASK.IBV_QP_RETRY_CNT |
                       MASK.IBV_QP_RNR_RETRY | MASK.IBV_QP_SQ_PSN | MASK.IBV_QP_MAX_QP_RD_ATOMIC)
        self.remote = remote

    def write(self, data: bytes, remote_offset: int = 0):
        self.mr.write(data, len(data))
        sge = SGE(self.mr.buf, len(data), self.mr.lkey)
        wr = SendWR(opcode=OP.IBV_WR_RDMA_WRITE, num_sge=1, sg=[sge])
        wr.set_wr_rdma(self.remote["rkey"], self.remote["addr"] + remote_offset)
        self.qp.post_send(wr)
        self._poll()

    def read_local(self, length: int, offset: int = 0) -> bytes:
        return self.mr.read(length, offset)

    def _poll(self):
        for _ in range(200000):
            npolled, wcs = self.cq.poll(1)
            if npolled:
                if wcs[0].status != WC.IBV_WC_SUCCESS:
                    raise RuntimeError(f"WC status {wcs[0].status}")
                return
        raise TimeoutError("no completion")


def exchange(sock: socket.socket, local: dict) -> dict:
    sock.sendall((json.dumps(local) + "\n").encode())
    buf = b""
    while b"\n" not in buf:
        buf += sock.recv(4096)
    return json.loads(buf.decode().strip())
