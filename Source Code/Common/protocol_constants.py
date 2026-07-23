# Network
TCP_CONTROL_PORT = 2121
BUFFER_SIZE = 4096
UDP_TIMEOUT = 2.0 # s, xài cho RDT retransmit
MAX_RETRIES = 5

# UDP custom header (5 trường bắt buộc)
# seq(4B) + ack(4B) + checksum(2B) + flags(1B) + length(2B) = 13 bytes
HEADER_FORMAT = "!IIHBH" # dùng với struct.pack/unpack
HEADER_SIZE = 13

# Flags (bitmask)
FLAG_DATA = 0x01
FLAG_ACK = 0x02
FLAG_FIN = 0x04
FLAG_LAST_CHUNK = 0x08
FLAG_RST = 0x10  # Dùng cho lệnh ABOR

# Approved FTP Commands (28 Lệnh)
CMD_USER = "USER"; CMD_PASS = "PASS"; CMD_QUIT = "QUIT"; CMD_NOOP = "NOOP"
CMD_PWD  = "PWD";  CMD_CWD  = "CWD";  CMD_CDUP = "CDUP"; CMD_MKD  = "MKD"
CMD_RMD  = "RMD";  CMD_LIST = "LIST"; CMD_NLST = "NLST"; CMD_STAT = "STAT"
CMD_SIZE = "SIZE"; CMD_MDTM = "MDTM"; CMD_TYPE = "TYPE"; CMD_MODE = "MODE"
CMD_PORT = "PORT"; CMD_PASV = "PASV"; CMD_RETR = "RETR"; CMD_STOR = "STOR"
CMD_STOU = "STOU"; CMD_APPE = "APPE"; CMD_DELE = "DELE"; CMD_RNFR = "RNFR"
CMD_RNTO = "RNTO"; CMD_HASH = "HASH"; CMD_ABOR = "ABOR"; CMD_HELP = "HELP"

# Three-digit FTP reply codes
REPLY_CODES = {
    125: "Data connection already open",
    150: "File status okay, opening data connection",
    200: "Command OK",
    220: "Service ready",
    221: "Goodbye",
    226: "Transfer complete",
    230: "Login successful",
    250: "Requested file action OK",
    331: "Username OK, need password",
    350: "Requested file action pending RNTO",
    421: "Service unavailable",
    425: "Can't open data connection",
    426: "Connection closed; transfer aborted",
    450: "File unavailable",
    500: "Syntax error",
    501: "Syntax error in parameters",
    502: "Command not implemented",
    530: "Not logged in",
    550: "File unavailable",
}