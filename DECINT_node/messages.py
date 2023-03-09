from dataclasses import dataclass
from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Dict, Union, Any, Literal

from ecdsa import VerifyingKey, SECP112r2


class MessageCat(Enum):  # Category
    TRANSACTION = 0
    BOOT = 1
    NODE_INFO = 2
    BLOCKCHAIN = 3
    MISCELLANEOUS = 4
    GET = 5
    NONE = -1


class StakeType(Enum):
    STAKE = 0
    UNSTAKE = 1


class GetType(Enum):
    NODES = 0
    STAKE_TRANS = 1
    BLOCKCHAIN = 2

class InfoType(Enum):
    HELLO = 0
    UPDATE = 0
    DELETE = 0


@dataclass
class Message(ABC):
    m_from: str
    #m_cat: MessageCat


class SignedMessage(Message):
    #m_cat: MessageCat

    @abstractmethod
    def check_sig(self) -> bool:
        pass


@dataclass
class TransMessage(SignedMessage):
    t_time: float
    sender: str
    receiver: str
    amount: float
    signature: str
    m_cat: MessageCat = MessageCat.TRANSACTION

    def check_sig(self) -> bool:
        check = f"{self.t_time} {self.sender} {self.receiver} {self.amount}"
        public_key = VerifyingKey.from_string(bytes.fromhex(self.sender), curve=SECP112r2)
        return public_key.verify(bytes.fromhex(self.signature), check.encode())


@dataclass
class StakeMessage(SignedMessage):
    s_type: StakeType
    t_time: float
    staker: str
    amount: float
    signature: str
    m_cat: MessageCat = MessageCat.TRANSACTION

    def check_sig(self) -> bool:
        public_key = VerifyingKey.from_string(bytes.fromhex(self.staker), curve=SECP112r2)
        return public_key.verify(bytes.fromhex(self.signature), str(self.t_time).encode())


@dataclass
class GetMessage(Message):
    g_type: GetType
    m_cat: MessageCat = MessageCat.GET


@dataclass
class NREQMessage(Message):
    node_list: List[Dict[str, Union[float, str, int]]]
    m_cat: MessageCat = MessageCat.BOOT


@dataclass
class BREQMessage(Message):
    chain: List[Any]  # cant be bother specifying
    m_cat: MessageCat = MessageCat.BOOT


@dataclass
class SREQMessage(Message):
    stake_list: List[List[Union[int, Dict[str, Union[float, str]]]]]
    m_cat: MessageCat = MessageCat.BOOT


@dataclass
class HelloMessage(SignedMessage):
    h_time: float
    i_type: InfoType
    wallet: str
    port: int
    version: float
    node_type: Literal["Lite", "Blockchain", "AI", "dist"]
    signature: str
    m_cat: MessageCat = MessageCat.NODE_INFO

    def check_sig(self) -> bool:
        public_key = VerifyingKey.from_string(bytes.fromhex(self.wallet), curve=SECP112r2)
        return public_key.verify(bytes.fromhex(self.signature), str(self.h_time).encode())


@dataclass
class UpdateMessage(SignedMessage):
    u_time: float
    i_type: InfoType
    old_wallet: str
    new_wallet: str
    port: int
    version: float
    signature: str
    m_cat: MessageCat = MessageCat.NODE_INFO

    def check_sig(self) -> bool:
        public_key = VerifyingKey.from_string(bytes.fromhex(self.old_wallet), curve=SECP112r2)
        return public_key.verify(bytes.fromhex(self.signature), str(self.u_time).encode())


@dataclass
class DeleteMessage(SignedMessage):
    d_time: float
    i_type: InfoType
    wallet: str
    signature: str
    m_cat: MessageCat = MessageCat.NODE_INFO

    def check_sig(self) -> bool:
        public_key = VerifyingKey.from_string(bytes.fromhex(self.wallet), curve=SECP112r2)
        return public_key.verify(bytes.fromhex(self.signature), str(self.d_time).encode())


@dataclass
class ValidMessage(Message):
    b_idx: int
    v_time: float
    valid_transactions: List[Union[List[Union[str, int]], Dict[str, Union[float, str]]]]
    m_cat: MessageCat = MessageCat.BLOCKCHAIN


@dataclass
class OnlineMessage(Message):
    m_cat: MessageCat = MessageCat.MISCELLANEOUS


@dataclass
class ErrorMessage(Message):
    error: str
    m_cat: MessageCat = MessageCat.MISCELLANEOUS


if __name__ == "__main__":
    message = TransMessage(m_from="Chris",
                           t_time=231838.213812938,
                           sender="Chris",
                           receiver="George",
                           amount=9023.32,
                           signature="chris"
                           )
    s_m = StakeMessage(m_from="Chris",
                       s_type=StakeType.STAKE,
                       t_time=318393.34234,
                       staker="Chris",
                       amount=1238123.4234,
                       signature="chris"
                       )
    print(message)
    print(s_m.s_type.name)
