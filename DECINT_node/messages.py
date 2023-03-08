from dataclasses import dataclass
from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Dict, Union, Any, Literal

from ecdsa import VerifyingKey, SECP112r2

class MessageCat(Enum): # Category
    TRANSACTION = 0
    BOOT = 1
    NODE_INFO = 2
    BLOCKCHAIN = 3
    MISCELLANEOUS = 4


class StakeType(Enum):
    STAKE = 0
    UNSTAKE = 1


class GetType(Enum):
    NODES = 0
    STAKE_TRANS = 1
    BLOCKCHAIN = 2


@dataclass
class Message(ABC):
    m_cat: MessageCat
    m_from: str


class SignedMessage(Message):
    @abstractmethod
    def check_sig(self) -> bool:
        pass


class TransMessage(SignedMessage):
    m_cat = MessageCat.TRANSACTION
    t_time: float
    sender: str
    receiver: str
    amount: float
    signature: str

    def check_sig(self) -> bool:
        check = f"{self.t_time} {self.sender} {self.receiver} {self.amount}"
        public_key = VerifyingKey.from_string(bytes.fromhex(self.sender), curve=SECP112r2)
        return public_key.verify(bytes.fromhex(self.signature), check.encode())


class StakeMessage(SignedMessage):
    m_cat = MessageCat.TRANSACTION
    s_type: StakeType
    t_time: float
    staker: str
    amount: float
    signature: str

    def check_sig(self) -> bool:
        public_key = VerifyingKey.from_string(bytes.fromhex(self.staker), curve=SECP112r2)
        return public_key.verify(bytes.fromhex(self.signature), str(self.t_time).encode())


class GetMessage(Message):
    m_cat = MessageCat.BOOT
    g_type = GetType


class NREQMessage(Message):
    m_cat = MessageCat.BOOT
    node_list: List[Dict[str, Union[float, str, int]]]


class BREQMessage(Message):
    m_cat = MessageCat.BOOT
    chain: List[Any]  # cant be bother specifying


class SREQMessage(Message):
    m_cat = MessageCat.BOOT
    stake_list: List[List[int, Dict[str, Union[float, str]]]]


class HelloMessage(SignedMessage):
    m_cat = MessageCat.NODE_INFO
    h_time: float
    wallet: str
    port: int
    version: float
    node_type: Literal["Lite", "Blockchain", "AI", "dist"]
    signature: str

    def check_sig(self) -> bool:
        public_key = VerifyingKey.from_string(bytes.fromhex(self.wallet), curve=SECP112r2)
        return public_key.verify(bytes.fromhex(self.signature), str(self.h_time).encode())


class UpdateMessage(SignedMessage):
    m_cat = MessageCat.NODE_INFO
    u_time: float
    old_wallet: str
    new_wallet: str
    port: int
    version: float
    signature: str

    def check_sig(self) -> bool:
        public_key = VerifyingKey.from_string(bytes.fromhex(self.old_wallet), curve=SECP112r2)
        return public_key.verify(bytes.fromhex(self.signature), str(self.u_time).encode())


class DeleteMessage(SignedMessage):
    m_cat = MessageCat.NODE_INFO
    d_time: float
    wallet: str
    signature: str

    def check_sig(self) -> bool:
        public_key = VerifyingKey.from_string(bytes.fromhex(self.wallet), curve=SECP112r2)
        return public_key.verify(bytes.fromhex(self.signature), str(self.d_time).encode())


class ValidMessage(Message):
    m_cat = MessageCat.BLOCKCHAIN
    b_idx: int
    v_time: float
    valid_transactions: List[List[str, int], Dict[str, Union[float, str]]]


class OnlineMessage(Message):
    m_cat = MessageCat.MISCELLANEOUS


class ErrorMessage(Message):
    m_cat = MessageCat.MISCELLANEOUS
    error: str

