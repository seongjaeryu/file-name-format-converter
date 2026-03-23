"""
파일명 포맷 컨버터 - 데스크톱 GUI (tkinter + 드래그앤드롭)
macOS 파일명을 Windows 호환 포맷으로 변환합니다.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys

from converter import convert_file, convert_filename

# tkinterdnd2 사용 가능 여부 확인
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False


class FileNameConverterApp:
    def __init__(self):
        if HAS_DND:
            self.root = TkinterDnD.Tk()
        else:
            self.root = tk.Tk()

        self.root.title("파일명 포맷 컨버터 (Mac → Windows)")
        self.root.geometry("700x500")
        self.root.minsize(600, 400)

        self.files: list[str] = []
        self.setup_ui()

    def setup_ui(self):
        # 상단 설명
        header = ttk.Frame(self.root, padding=10)
        header.pack(fill=tk.X)

        ttk.Label(
            header,
            text="파일명 포맷 컨버터",
            font=("Helvetica", 18, "bold"),
        ).pack()
        ttk.Label(
            header,
            text="macOS 파일명을 Windows 호환 포맷(NFC)으로 변환합니다",
            font=("Helvetica", 12),
        ).pack(pady=(2, 0))

        # 드래그앤드롭 영역
        drop_frame = ttk.LabelFrame(self.root, text="파일 추가", padding=10)
        drop_frame.pack(fill=tk.X, padx=10, pady=5)

        self.drop_label = tk.Label(
            drop_frame,
            text="여기에 파일을 드래그 & 드롭 하세요\n또는 아래 버튼으로 파일 선택",
            bg="#f0f0f0",
            fg="#666",
            font=("Helvetica", 13),
            height=4,
            relief="groove",
            borderwidth=2,
        )
        self.drop_label.pack(fill=tk.X, pady=5)

        if HAS_DND:
            self.drop_label.drop_target_register(DND_FILES)
            self.drop_label.dnd_bind("<<Drop>>", self.on_drop)
            self.drop_label.dnd_bind("<<DragEnter>>", self.on_drag_enter)
            self.drop_label.dnd_bind("<<DragLeave>>", self.on_drag_leave)
        else:
            self.drop_label.config(
                text="파일 선택 버튼을 눌러 파일을 추가하세요\n(드래그앤드롭: pip install tkinterdnd2)"
            )

        btn_frame = ttk.Frame(drop_frame)
        btn_frame.pack(fill=tk.X, pady=5)

        ttk.Button(btn_frame, text="파일 선택...", command=self.select_files).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(btn_frame, text="폴더 선택...", command=self.select_folder).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(btn_frame, text="목록 초기화", command=self.clear_files).pack(
            side=tk.RIGHT, padx=5
        )

        # 파일 목록
        list_frame = ttk.LabelFrame(self.root, text="변환 대상 파일 목록", padding=5)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        columns = ("original", "converted", "status")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=8)
        self.tree.heading("original", text="원래 파일명")
        self.tree.heading("converted", text="변환 후 파일명")
        self.tree.heading("status", text="상태")
        self.tree.column("original", width=250)
        self.tree.column("converted", width=250)
        self.tree.column("status", width=100)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 하단 버튼
        bottom = ttk.Frame(self.root, padding=10)
        bottom.pack(fill=tk.X)

        self.status_label = ttk.Label(bottom, text="파일을 추가해주세요", font=("Helvetica", 11))
        self.status_label.pack(side=tk.LEFT)

        self.convert_btn = ttk.Button(
            bottom, text="변환 실행", command=self.convert_all, state=tk.DISABLED
        )
        self.convert_btn.pack(side=tk.RIGHT, padx=5)

    def on_drag_enter(self, event):
        self.drop_label.config(bg="#d4edda", fg="#155724")

    def on_drag_leave(self, event):
        self.drop_label.config(bg="#f0f0f0", fg="#666")

    def on_drop(self, event):
        self.drop_label.config(bg="#f0f0f0", fg="#666")
        # tkinterdnd2는 공백이 포함된 경로를 중괄호로 감싸서 전달
        raw = event.data
        paths = []
        i = 0
        while i < len(raw):
            if raw[i] == "{":
                end = raw.index("}", i)
                paths.append(raw[i + 1 : end])
                i = end + 2
            elif raw[i] == " ":
                i += 1
            else:
                end = raw.find(" ", i)
                if end == -1:
                    end = len(raw)
                paths.append(raw[i:end])
                i = end + 1
        self.add_files(paths)

    def select_files(self):
        paths = filedialog.askopenfilenames(title="변환할 파일 선택")
        if paths:
            self.add_files(list(paths))

    def select_folder(self):
        folder = filedialog.askdirectory(title="변환할 폴더 선택")
        if folder:
            paths = []
            for entry in os.listdir(folder):
                full = os.path.join(folder, entry)
                if os.path.isfile(full):
                    paths.append(full)
            if paths:
                self.add_files(paths)
            else:
                messagebox.showinfo("알림", "폴더에 파일이 없습니다.")

    def add_files(self, paths: list[str]):
        for path in paths:
            if not os.path.isfile(path):
                continue
            if path in self.files:
                continue
            self.files.append(path)
            old_name = os.path.basename(path)
            new_name = convert_filename(old_name)
            status = "변환 필요" if old_name != new_name else "변환 불필요"
            self.tree.insert("", tk.END, values=(old_name, new_name, status))

        count = len(self.files)
        self.status_label.config(text=f"총 {count}개 파일")
        self.convert_btn.config(state=tk.NORMAL if count > 0 else tk.DISABLED)

    def clear_files(self):
        self.files.clear()
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.status_label.config(text="파일을 추가해주세요")
        self.convert_btn.config(state=tk.DISABLED)

    def convert_all(self):
        converted = 0
        skipped = 0
        errors = []

        items = self.tree.get_children()
        for i, item in enumerate(items):
            filepath = self.files[i]
            try:
                old_name, new_name, changed = convert_file(filepath)
                if changed:
                    self.tree.set(item, "converted", new_name)
                    self.tree.set(item, "status", "변환 완료 ✓")
                    # 파일 경로 갱신
                    self.files[i] = os.path.join(os.path.dirname(filepath), new_name)
                    converted += 1
                else:
                    self.tree.set(item, "status", "변환 불필요")
                    skipped += 1
            except Exception as e:
                self.tree.set(item, "status", f"오류: {e}")
                errors.append((os.path.basename(filepath), str(e)))

        msg = f"변환 완료: {converted}개 | 변환 불필요: {skipped}개"
        if errors:
            msg += f" | 오류: {len(errors)}개"
        self.status_label.config(text=msg)

        if errors:
            error_detail = "\n".join(f"  - {name}: {err}" for name, err in errors)
            messagebox.showwarning("변환 오류", f"일부 파일 변환 중 오류:\n{error_detail}")
        elif converted > 0:
            messagebox.showinfo("완료", f"{converted}개 파일의 이름이 변환되었습니다.")
        else:
            messagebox.showinfo("완료", "변환이 필요한 파일이 없습니다.")

    def run(self):
        self.root.mainloop()


def main():
    app = FileNameConverterApp()
    app.run()


if __name__ == "__main__":
    main()
