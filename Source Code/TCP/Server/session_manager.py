"""
session_manager.py
"""

import threading


class Session:
    def __init__(self, addr):
        self.addr = addr                     
        self.client_id = f"{addr[0]}:{addr[1]}"

        # Xác thực 
        self.pending_user = None
        self.authenticated_user = None

        # Duyệt thư mục 
        self.cwd = "/"


        self.transfer_type = "A"  
        self.transfer_mode = "S"  


        self.data_mode = None        
        self.data_addr = None       
        self.pasv_socket = None      
        self.pasv_port = None       


        self.rename_from = None      


        self.commands_executed = 0

    def is_authenticated(self) -> bool:
        return self.authenticated_user is not None

    def close_data_channel(self):

        if self.pasv_socket is not None:
            try:
                self.pasv_socket.close()
            except OSError:
                pass
        self.data_mode = None
        self.data_addr = None
        self.pasv_socket = None
        self.pasv_port = None


class SessionManager:


    def __init__(self):
        self._sessions = {}  
        self._lock = threading.Lock()

    def get_or_create(self, addr) -> Session:
        with self._lock:
            if addr not in self._sessions:
                self._sessions[addr] = Session(addr)
            return self._sessions[addr]

    def get(self, addr):
        with self._lock:
            return self._sessions.get(addr)

    def remove(self, addr):
        with self._lock:
            session = self._sessions.pop(addr, None)
            if session:
                session.close_data_channel()

    def active_sessions(self):

        with self._lock:
            return list(self._sessions.values())

    def session_table_text(self) -> str:

        sessions = self.active_sessions()
        if not sessions:
            return "No active sessions."
        lines = [f"Active sessions: {len(sessions)}"]
        for s in sessions:
            user = s.authenticated_user or "(chua dang nhap)"
            lines.append(
                f"  - {s.client_id:22} user={user:12} cwd={s.cwd:10} "
                f"mode={s.data_mode or '-':8} cmds={s.commands_executed}"
            )
        return "\n".join(lines)


session_manager = SessionManager()