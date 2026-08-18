"""
QuoteRenamer - 견적서/거래명세서/세금계산서 PDF 리네이머 데스크탑 앱
==================================
PDF를 창에 끌어다 놓으면(또는 선택하면) 자동으로 이름을 제안하고,
확인/수정 후 '적용'을 누르면 실제로 이름이 바뀝니다.

실행:
    python app.py

필요 패키지:
    pip install pdfplumber tkinterdnd2
    (tkinterdnd2가 없어도 실행은 되지만, 그 경우 드래그&드롭 대신
     '파일 선택' 버튼만 쓸 수 있습니다.)
"""
import shutil
import sys
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False

import quote_renamer as qr  # 이 파일과 같은 폴더에 있어야 합니다

APP_NAME = "QuoteRenamer"
APP_VERSION = "1.2.0"
APP_RELEASE_DATE = "2026-08-18"
APP_AUTHOR = "강무엽"


def _known_folder(data1, data2, data3, data4, fallback_name: str) -> Path:
    """Windows 공식 API(SHGetKnownFolderPath)로 사용자 폴더 실제 위치를 찾는다.
    (사용자 이름이나 특정 PC 경로를 하드코딩하지 않음 — 다른 사람 PC에서도,
    회사 정책 등으로 폴더가 다른 드라이브로 리다이렉트된 PC에서도 동작해야
    하기 때문)"""
    if sys.platform == "win32":
        try:
            import ctypes
            from ctypes import wintypes

            class GUID(ctypes.Structure):
                _fields_ = [
                    ("Data1", wintypes.DWORD),
                    ("Data2", wintypes.WORD),
                    ("Data3", wintypes.WORD),
                    ("Data4", ctypes.c_ubyte * 8),
                ]

            folder_id = GUID(data1, data2, data3, (ctypes.c_ubyte * 8)(*data4))
            path_ptr = ctypes.c_wchar_p()
            hresult = ctypes.windll.shell32.SHGetKnownFolderPath(
                ctypes.byref(folder_id), 0, 0, ctypes.byref(path_ptr)
            )
            if hresult == 0 and path_ptr.value:
                path = Path(path_ptr.value)
                ctypes.windll.ole32.CoTaskMemFree(path_ptr)
                return path
        except Exception:
            pass
    return Path.home() / fallback_name


def get_downloads_dir() -> Path:
    # FOLDERID_Downloads
    return _known_folder(
        0x374DE290, 0x123F, 0x4565,
        (0x91, 0x64, 0x39, 0xC4, 0x92, 0x5E, 0x46, 0x7B),
        "Downloads",
    )


def get_documents_dir() -> Path:
    # FOLDERID_Documents
    return _known_folder(
        0xFDD39AD0, 0x238F, 0x46AF,
        (0xAD, 0xB4, 0x6C, 0x85, 0x48, 0x03, 0x69, 0xC7),
        "Documents",
    )


def get_resource_path(name: str) -> Path:
    """아이콘처럼 exe 안에 번들된(읽기 전용) 리소스 파일 경로.
    company_aliases.json/tesseract처럼 사용자가 수정해야 하는 파일은
    get_app_dir()을 쓰고, 이 함수는 절대 안 바뀌는 정적 자산에만 쓴다."""
    if getattr(sys, "frozen", False):
        base = Path(getattr(sys, "_MEIPASS", qr.get_app_dir()))
    else:
        base = Path(__file__).parent
    return base / name


def show_splash(root) -> tk.Toplevel:
    splash = tk.Toplevel(root)
    splash.overrideredirect(True)
    splash.configure(bg="#4f46e5")
    w, h = 420, 280
    x = (splash.winfo_screenwidth() - w) // 2
    y = (splash.winfo_screenheight() - h) // 2
    splash.geometry(f"{w}x{h}+{x}+{y}")

    try:
        from PIL import Image, ImageTk
        img = Image.open(get_resource_path("icon.ico")).resize((96, 96))
        logo = ImageTk.PhotoImage(img)
        logo_label = tk.Label(splash, image=logo, bg="#4f46e5")
        logo_label.image = logo  # 참조 유지 (안 하면 GC로 사라짐)
        logo_label.pack(pady=(32, 10))
    except Exception:
        pass

    tk.Label(splash, text=APP_NAME, font=("Segoe UI", 20, "bold"),
             fg="white", bg="#4f46e5").pack()
    tk.Label(splash, text=f"v{APP_VERSION}  ·  {APP_RELEASE_DATE}",
             font=("Malgun Gothic", 10), fg="#c7d2fe", bg="#4f46e5").pack(pady=(6, 0))
    tk.Label(splash, text=f"제작: {APP_AUTHOR}",
             font=("Malgun Gothic", 10), fg="#c7d2fe", bg="#4f46e5").pack(pady=(2, 0))

    splash.update()
    return splash


class RenamerApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} — 견적서/거래명세서/세금계산서 PDF 리네이머")
        self.root.geometry("900x560")
        self.aliases = qr.load_aliases()
        self.rows = {}  # tree iid -> {"src": Path}

        self._build_ui()

    # ── UI 구성 ──────────────────────────────────────────────
    def _build_ui(self):
        top = tk.Frame(self.root, bg="#eef2ff", height=90)
        top.pack(fill="x", padx=10, pady=10)
        top.pack_propagate(False)

        if DND_AVAILABLE:
            drop_text = "여기에 PDF를 끌어다 놓으세요\n(견적서/거래명세서/세금계산서 자동 인식, 또는 클릭해서 선택)"
        else:
            drop_text = (
                "드래그&드롭을 쓰려면 'pip install tkinterdnd2' 후 다시 실행하세요.\n"
                "지금은 아래 '파일 선택' 버튼을 이용하세요."
            )
        self.drop_label = tk.Label(
            top, text=drop_text, bg="#eef2ff", fg="#334155",
            font=("Malgun Gothic", 11), cursor="hand2", justify="center",
        )
        self.drop_label.pack(expand=True, fill="both")
        self.drop_label.bind("<Button-1>", lambda e: self.browse_files())

        if DND_AVAILABLE:
            for widget in (top, self.drop_label):
                widget.drop_target_register(DND_FILES)
                widget.dnd_bind("<<Drop>>", self.on_drop)

        btn_bar = tk.Frame(self.root)
        btn_bar.pack(fill="x", padx=10)
        tk.Button(btn_bar, text="+ 파일 선택", command=self.browse_files).pack(side="left")
        tk.Button(btn_bar, text="+ 폴더 전체 추가", command=self.browse_folder).pack(side="left", padx=6)
        tk.Button(btn_bar, text="목록 지우기", command=self.clear_list).pack(side="left")

        self.out_mode = tk.StringVar(value="copy")
        tk.Radiobutton(btn_bar, text="새 폴더에 복사 (원본 보존)", variable=self.out_mode,
                        value="copy").pack(side="left", padx=(20, 4))
        tk.Radiobutton(btn_bar, text="원본 이름 바로 변경", variable=self.out_mode,
                        value="rename").pack(side="left")

        columns = ("orig", "proposed", "status")
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings", height=14)
        self.tree.heading("orig", text="원본 파일명")
        self.tree.heading("proposed", text="제안 파일명 (더블클릭으로 수정)")
        self.tree.heading("status", text="상태")
        self.tree.column("orig", width=260)
        self.tree.column("proposed", width=440)
        self.tree.column("status", width=150)
        self.tree.pack(fill="both", expand=True, padx=10, pady=(10, 0))
        self.tree.bind("<Double-1>", self.on_edit_cell)

        if DND_AVAILABLE:
            self.tree.drop_target_register(DND_FILES)
            self.tree.dnd_bind("<<Drop>>", self.on_drop)

        bottom = tk.Frame(self.root)
        bottom.pack(fill="x", padx=10, pady=10)
        self.out_dir_var = tk.StringVar(value=str(get_documents_dir()))
        tk.Entry(bottom, textvariable=self.out_dir_var, width=58).pack(side="left")
        tk.Button(bottom, text="출력 폴더 선택", command=self.browse_out_dir).pack(side="left", padx=6)
        tk.Button(bottom, text="적용", bg="#4f46e5", fg="white",
                  command=self.apply_all).pack(side="right")
        tk.Label(
            self.root,
            text="'새 폴더에 복사' 선택 시, 위 폴더 아래에 문서종류별로"
                 "(견적서/거래명세서/세금계산서) 하위 폴더를 만들어 저장합니다.",
            fg="#64748b", font=("Malgun Gothic", 8),
        ).pack(fill="x", padx=10, pady=(0, 6))

    # ── 파일 추가 ────────────────────────────────────────────
    def browse_files(self):
        paths = filedialog.askopenfilenames(filetypes=[("PDF files", "*.pdf")])
        self.add_files(paths)

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.add_files([str(p) for p in Path(folder).glob("*.pdf")])

    def browse_out_dir(self):
        folder = filedialog.askdirectory()
        if folder:
            self.out_dir_var.set(folder)

    def on_drop(self, event):
        paths = self.root.tk.splitlist(event.data)
        pdfs = []
        for p in paths:
            pp = Path(p)
            if pp.is_dir():
                pdfs.extend(str(x) for x in pp.glob("*.pdf"))
            elif pp.suffix.lower() == ".pdf":
                pdfs.append(str(pp))
        self.add_files(pdfs)

    def add_files(self, paths):
        existing = {row["src"] for row in self.rows.values()}
        for p in paths:
            p = Path(p)
            if not p.exists() or p.suffix.lower() != ".pdf" or p in existing:
                continue
            self.process_and_insert(p)

    # ── 처리 ────────────────────────────────────────────────
    def process_and_insert(self, path: Path):
        doc_type = "견적서"
        try:
            text, tables = qr.read_pdf(path)
            doc_type, w0 = qr.detect_doc_type(text)
            company, w1 = qr.extract_company(text, tables, self.aliases)
            date, w2 = qr.extract_date(text)
            first_item, item_count, w3 = qr.extract_items(tables)
            proposed = qr.build_filename(doc_type, company, date, first_item, item_count)
            warn = "; ".join(w for w in [w0, w1, w2, w3] if w)
            status = warn if warn else "OK"
        except Exception as e:
            proposed = path.name
            status = f"오류: {e}"

        iid = self.tree.insert("", "end", values=(path.name, proposed, status))
        self.rows[iid] = {"src": path, "doc_type": doc_type}

    def on_edit_cell(self, event):
        item = self.tree.identify_row(event.y)
        col = self.tree.identify_column(event.x)
        if not item or col != "#2":
            return
        bbox = self.tree.bbox(item, col)
        if not bbox:
            return
        x, y, w, h = bbox
        value = self.tree.set(item, "proposed")
        entry = tk.Entry(self.tree)
        entry.insert(0, value)
        entry.select_range(0, "end")
        entry.place(x=x, y=y, width=w, height=h)
        entry.focus()

        def save(_=None):
            self.tree.set(item, "proposed", entry.get())
            entry.destroy()

        entry.bind("<Return>", save)
        entry.bind("<FocusOut>", save)

    def clear_list(self):
        self.tree.delete(*self.tree.get_children())
        self.rows.clear()

    # ── 적용 ────────────────────────────────────────────────
    def apply_all(self):
        items = self.tree.get_children()
        if not items:
            messagebox.showinfo("알림", "추가된 PDF가 없습니다.")
            return

        mode = self.out_mode.get()
        out_base = Path(self.out_dir_var.get())

        used_by_dir = {}  # dest_dir -> 이번 실행에서 이미 쓴 파일명 집합
        dest_dirs_used = set()
        ok_count = 0
        for iid in items:
            src = self.rows[iid]["src"]
            doc_type = self.rows[iid].get("doc_type", "견적서")
            target_name = self.tree.set(iid, "proposed")
            if "." in target_name:
                stem, ext = target_name.rsplit(".", 1)
            else:
                stem, ext = target_name, "pdf"

            if mode == "copy":
                # 문서종류별 하위 폴더(견적서/거래명세서/세금계산서)에 차곡차곡 저장
                dest_dir = out_base / doc_type
                dest_dir.mkdir(parents=True, exist_ok=True)
            else:
                dest_dir = src.parent
            dest_dirs_used.add(dest_dir)

            used = used_by_dir.setdefault(dest_dir, set())
            candidate = target_name
            n = 1
            while candidate in used or (dest_dir / candidate).exists():
                n += 1
                candidate = f"{stem}_{n}.{ext}"
            used.add(candidate)
            dst = dest_dir / candidate

            try:
                if mode == "copy":
                    shutil.copy2(src, dst)
                else:
                    src.rename(dst)
                self.tree.set(iid, "status", "완료 ✅")
                ok_count += 1
            except Exception as e:
                self.tree.set(iid, "status", f"실패: {e}")

        if mode == "copy":
            location = "\n".join(f"- {d}" for d in sorted(dest_dirs_used))
        else:
            location = "원본 폴더"

        messagebox.showinfo(
            "완료",
            f"{ok_count}/{len(items)}개 처리 완료.\n저장 위치:\n{location}",
        )


def main():
    root = TkinterDnD.Tk() if DND_AVAILABLE else tk.Tk()
    root.withdraw()
    splash = show_splash(root)

    def start_app():
        splash.destroy()
        RenamerApp(root)
        root.deiconify()

    root.after(1600, start_app)
    root.mainloop()


if __name__ == "__main__":
    main()
