from deepagents.backends.protocol import (BackendProtocol, WriteResult, EditResult, LsResult, ReadResult, GrepResult, GlobResult)


class PolicyWrapper(BackendProtocol):
    def __init__(self,inner:BackendProtocol, deny_prefix:list[str] | None = None):
        self.inner = inner
        #self.deny_prefix = [p if p.endswith("/") else p + "/" for p in (deny_prefix or [])]
        self.deny_prefix = deny_prefix or []

    def _deny(self,path:str) -> bool:
        return any(path == p or path.startswith(p + "/") for p in self.deny_prefix)

    def ls(self,path:str) -> LsResult:
        return self.inner.ls(path)

    def read(self,file_path:str,offset:int = 0, limit:int= 2000) -> ReadResult:
        print("READ PATHS",file_path)
        return self.inner.read(file_path, offset=offset, limit=limit)

    def grep(self, pattern: str, path: str | None = None, glob: str | None = None) -> GrepResult:
        return self.inner.grep(pattern, path, glob)

    def glob(self, pattern: str, path: str | None = None) -> GlobResult:
        return self.inner.glob(pattern, path)

    def write(self, file_path: str, content: str) -> WriteResult:
        print("MEMORY Write",file_path)
        if self._deny(file_path):
            return WriteResult(error=f"Writes are not allowed under {file_path}")
        return self.inner.write(file_path, content)
    
    def edit(self, file_path: str, old_string: str, new_string: str, replace_all: bool = False) -> EditResult:
        if self._deny(file_path):
            return EditResult(error=f"Edits are not allowed under {file_path}")
        return self.inner.edit(file_path, old_string, new_string, replace_all)

    def download_files(self, paths: list[str]):
        print("POLICY DOWNLOAD PATHS:", paths)
        return self.inner.download_files(paths)






