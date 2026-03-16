import argparse
import io
import sys
import time
from pathlib import Path
from typing import List, Optional

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox

try:
	import win32print
	import win32api
except ImportError:
	win32print = None
	win32api = None


# Configurar saida UTF-8 no Windows (apenas se ainda não foi configurado)
if sys.platform == "win32":
	try:
		if not isinstance(sys.stdout, io.TextIOWrapper) or sys.stdout.encoding != "utf-8":
			sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
		if not isinstance(sys.stderr, io.TextIOWrapper) or sys.stderr.encoding != "utf-8":
			sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
	except Exception:
		pass  # Já configurado ou não é necessário


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(
		description="Imprime PDFs em massa usando impressora padrao do Windows."
	)
	parser.add_argument(
		"--input",
		help="Pasta com PDFs ou caminho de um arquivo PDF.",
	)
	parser.add_argument(
		"--gui",
		action="store_true",
		help="Abre interface grafica para selecionar arquivos/pasta e opcoes.",
	)
	parser.add_argument(
		"--recursive",
		action="store_true",
		help="Busca PDFs em subpastas quando --input for diretorio.",
	)
	parser.add_argument(
		"--duplex",
		choices=["on", "off"],
		default="on",
		help="Impressao frente e verso (padrao: on).",
	)
	parser.add_argument(
		"--grayscale",
		choices=["on", "off"],
		default="on",
		help="Impressao preto e branco (padrao: on).",
	)
	parser.add_argument(
		"--pause-between-files",
		type=float,
		default=1.5,
		help="Pausa entre arquivos para reduzir falhas de spool.",
	)
	return parser.parse_args()


def ask_selection_gui(default_pause: float) -> Optional[dict]:
	selection_mode = {"kind": None, "value": None}
	result = {"payload": None}

	# Configurar tema
	ctk.set_appearance_mode("dark")
	ctk.set_default_color_theme("blue")

	root = ctk.CTk()
	root.title("Impressao em Massa - PDFs")
	root.resizable(False, False)
	
	# Centralizar janela na tela
	window_width = 800
	window_height = 560
	
	root.update_idletasks()
	screen_width = root.winfo_screenwidth()
	screen_height = root.winfo_screenheight()
	
	x = (screen_width - window_width) // 2
	y = (screen_height - window_height) // 2
	
	root.geometry(f"{window_width}x{window_height}+{x}+{y}")

	main = ctk.CTkFrame(root)
	main.pack(fill="both", expand=True, padx=20, pady=20)

	title = ctk.CTkLabel(main, text="Selecionar PDFs para impressao", font=ctk.CTkFont(size=18, weight="bold"))
	title.pack(anchor="w", pady=(0, 10))

	info = ctk.CTkLabel(
		main,
		text="A impressao sera enviada para a impressora padrao do Windows.",
		font=ctk.CTkFont(size=12)
	)
	info.pack(anchor="w", pady=(0, 12))

	selected_label = ctk.CTkLabel(main, text="Nenhum arquivo/pasta selecionado.", font=ctk.CTkFont(size=12))
	selected_label.pack(anchor="w", pady=(0, 8))

	# Usar CTkTextbox como lista de arquivos (readonly)
	listbox = ctk.CTkTextbox(main, height=150, width=750, font=ctk.CTkFont(size=11))
	listbox.pack(fill="x", pady=(0, 12))

	button_row = ctk.CTkFrame(main, fg_color="transparent")
	button_row.pack(fill="x", pady=(0, 12))

	def refresh_selection_preview() -> None:
		listbox.configure(state="normal")
		listbox.delete("1.0", "end")
		if selection_mode["kind"] == "files":
			files = selection_mode["value"]
			selected_label.configure(text=f"{len(files)} arquivo(s) PDF selecionado(s).")
			for path in files:
				listbox.insert("end", str(path) + "\n")
		elif selection_mode["kind"] == "folder":
			folder = selection_mode["value"]
			selected_label.configure(text=f"Pasta selecionada: {folder}")
			listbox.insert("end", str(folder) + "\n")
		else:
			selected_label.configure(text="Nenhum arquivo/pasta selecionado.")
		listbox.configure(state="disabled")

	def select_files() -> None:
		paths = filedialog.askopenfilenames(
			title="Selecione um ou mais arquivos PDF",
			filetypes=[("PDF", "*.pdf")],
		)
		if not paths:
			return
		selection_mode["kind"] = "files"
		selection_mode["value"] = [Path(p).resolve() for p in paths]
		refresh_selection_preview()

	def select_folder() -> None:
		path = filedialog.askdirectory(title="Selecione a pasta com PDFs")
		if not path:
			return
		selection_mode["kind"] = "folder"
		selection_mode["value"] = Path(path).resolve()
		refresh_selection_preview()

	def clear_selection() -> None:
		selection_mode["kind"] = None
		selection_mode["value"] = None
		refresh_selection_preview()

	ctk.CTkButton(button_row, text="Selecionar PDFs", command=select_files, width=140).pack(side="left", padx=(0, 8))
	ctk.CTkButton(button_row, text="Selecionar Pasta", command=select_folder, width=140).pack(side="left", padx=(0, 8))
	ctk.CTkButton(button_row, text="Limpar", command=clear_selection, width=100).pack(side="left")

	options_frame = ctk.CTkFrame(main)
	options_frame.pack(fill="x", pady=(0, 12), padx=5)

	options_label = ctk.CTkLabel(options_frame, text="Opcoes de impressao", font=ctk.CTkFont(size=14, weight="bold"))
	options_label.grid(row=0, column=0, columnspan=3, sticky="w", padx=10, pady=(10, 15))

	duplex_var = tk.BooleanVar(value=True)
	grayscale_var = tk.BooleanVar(value=True)
	recursive_var = tk.BooleanVar(value=True)
	pause_var = tk.StringVar(value=str(default_pause))

	ctk.CTkCheckBox(options_frame, text="Frente e verso", variable=duplex_var).grid(row=1, column=0, sticky="w", padx=(10, 16), pady=5)
	ctk.CTkCheckBox(options_frame, text="Preto e branco", variable=grayscale_var).grid(row=1, column=1, sticky="w", padx=(0, 16), pady=5)
	ctk.CTkCheckBox(options_frame, text="Buscar em subpastas", variable=recursive_var).grid(row=1, column=2, sticky="w", padx=(0, 10), pady=5)

	ctk.CTkLabel(options_frame, text="Pausa entre arquivos (s):").grid(row=2, column=0, sticky="w", padx=10, pady=(10, 10))
	ctk.CTkEntry(options_frame, width=100, textvariable=pause_var).grid(row=2, column=1, sticky="w", pady=(10, 10))

	action_row = ctk.CTkFrame(main, fg_color="transparent")
	action_row.pack(fill="x", pady=(10, 0))

	def submit() -> None:
		if selection_mode["kind"] not in {"files", "folder"}:
			messagebox.showwarning("Selecao obrigatoria", "Selecione arquivos PDF ou uma pasta.")
			return

		try:
			pause_between = float(pause_var.get().replace(",", "."))
		except ValueError:
			messagebox.showerror("Valores invalidos", "Informe valor numerico para pausa entre arquivos.")
			return

		if pause_between < 0:
			messagebox.showerror("Valores invalidos", "Tempo nao pode ser negativo.")
			return

		result["payload"] = {
			"kind": selection_mode["kind"],
			"value": selection_mode["value"],
			"recursive": recursive_var.get(),
			"duplex_on": duplex_var.get(),
			"grayscale_on": grayscale_var.get(),
			"pause_between_files": pause_between,
		}
		root.destroy()

	def cancel() -> None:
		result["payload"] = None
		root.destroy()

	ctk.CTkButton(action_row, text="Imprimir", command=submit, width=120, height=35, font=ctk.CTkFont(size=13, weight="bold")).pack(side="right")
	ctk.CTkButton(action_row, text="Cancelar", command=cancel, width=120, height=35, fg_color="gray", hover_color="#5a5a5a").pack(side="right", padx=(0, 8))

	root.protocol("WM_DELETE_WINDOW", cancel)
	root.mainloop()
	return result["payload"]


def collect_pdf_files(input_path: Path, recursive: bool) -> List[Path]:
	if input_path.is_file():
		if input_path.suffix.lower() != ".pdf":
			raise ValueError(f"Arquivo informado nao e PDF: {input_path}")
		return [input_path]

	if not input_path.is_dir():
		raise ValueError(f"Caminho invalido: {input_path}")

	pattern = "**/*.pdf" if recursive else "*.pdf"
	files = sorted(path for path in input_path.glob(pattern) if path.is_file())
	return files


def configure_printer_settings(printer_name: str, duplex_on: bool, grayscale_on: bool) -> None:
	"""Configura as preferencias da impressora via win32print"""
	if not win32print:
		return
	
	try:
		handle = win32print.OpenPrinter(printer_name)
		try:
			# Obter configuracoes atuais
			properties = win32print.GetPrinter(handle, 2)
			pDevMode = properties["pDevMode"]
			
			if pDevMode:
				# Configurar duplex (frente e verso)
				if duplex_on:
					pDevMode.Duplex = 2  # DMDUP_VERTICAL (long edge)
				else:
					pDevMode.Duplex = 1  # DMDUP_SIMPLEX (single-sided)
				
				# Configurar cor (preto e branco)
				if grayscale_on:
					pDevMode.Color = 2  # DMCOLOR_MONOCHROME
				else:
					pDevMode.Color = 1  # DMCOLOR_COLOR
				
				# Aplicar configuracoes
				properties["pDevMode"] = pDevMode
				win32print.SetPrinter(handle, 2, properties, 0)
		finally:
			win32print.ClosePrinter(handle)
	except Exception as exc:
		print(f"⚠️ Aviso: nao foi possivel configurar impressora ({exc})")





def print_pdf_direct(pdf_path: Path, printer_name: str) -> bool:
	"""Imprime PDF usando win32api.ShellExecute (abre leitor PDF padrao)"""
	try:
		# ShellExecute usa o verbo "print" e o leitor PDF associado
		result = win32api.ShellExecute(
			0,
			"print",
			str(pdf_path.resolve()),
			f'/d:"{printer_name}"',
			".",
			0  # SW_HIDE
		)
		# ShellExecute retorna um valor > 32 se bem-sucedido
		return result > 32
	except Exception as exc:
		print(f"   ❌ Erro ao imprimir {pdf_path.name}: {exc}")
		return False


def print_pdf_batch(
	files: List[Path],
	duplex_on: bool,
	grayscale_on: bool,
	pause_between_files: float,
) -> int:
	"""Imprime PDFs usando API Windows"""
	if not win32print or not win32api:
		raise RuntimeError(
			"Biblioteca pywin32 nao instalada. "
			"Instale com: pip install pywin32"
		)
	
	# Obter impressora padrao
	printer_name = win32print.GetDefaultPrinter()
	print(f"Impressora: {printer_name}")
	
	# Configurar preferencias da impressora
	configure_printer_settings(printer_name, duplex_on, grayscale_on)
	
	printed = 0
	for index, pdf_path in enumerate(files, start=1):
		print(f"[{index}/{len(files)}] Imprimindo: {pdf_path.name}")
		
		if print_pdf_direct(pdf_path, printer_name):
			printed += 1
			print(f"   ✓ Enviado para impressora")
		
		# Aguardar entre arquivos para evitar sobrecarga do spooler
		if index < len(files):
			time.sleep(pause_between_files)
	
	return printed


def run_print_job(
	files: List[Path],
	duplex_on: bool,
	grayscale_on: bool,
	pause_between_files: float,
) -> None:
	print("=" * 68)
	print("IMPRESSAO EM MASSA - DIRETO")
	print("=" * 68)
	print(f"Arquivos encontrados: {len(files)}")
	print(f"Frente e verso: {'ON' if duplex_on else 'OFF'}")
	print(f"Preto e branco: {'ON' if grayscale_on else 'OFF'}")
	print("Impressora: padrao do Windows")
	print("=" * 68)

	try:
		total_printed = print_pdf_batch(
			files=files,
			duplex_on=duplex_on,
			grayscale_on=grayscale_on,
			pause_between_files=pause_between_files,
		)
	except RuntimeError as exc:
		print(f"❌ {exc}")
		raise SystemExit(1)
	except Exception as exc:
		print(f"❌ Erro durante impressao: {exc}")
		raise SystemExit(1)

	print("=" * 68)
	print(f"✅ Impressao enviada para {total_printed} arquivo(s).")
	print("=" * 68)


def main() -> None:
	args = parse_args()
	if args.gui or not args.input:
		payload = ask_selection_gui(default_pause=args.pause_between_files)
		if payload is None:
			print("⚠️ Operacao cancelada pelo usuario.")
			raise SystemExit(1)

		if payload["kind"] == "files":
			files = payload["value"]
		else:
			folder_path = payload["value"]
			try:
				files = collect_pdf_files(input_path=folder_path, recursive=payload["recursive"])
			except ValueError as exc:
				print(f"❌ {exc}")
				raise SystemExit(1)

		if not files:
			print("⚠️ Nenhum PDF encontrado para impressao.")
			raise SystemExit(1)

		run_print_job(
			files=files,
			duplex_on=payload["duplex_on"],
			grayscale_on=payload["grayscale_on"],
			pause_between_files=payload["pause_between_files"],
		)
		return

	input_path = Path(args.input).expanduser().resolve()
	try:
		files = collect_pdf_files(input_path=input_path, recursive=args.recursive)
	except ValueError as exc:
		print(f"❌ {exc}")
		raise SystemExit(1)

	if not files:
		print("⚠️ Nenhum PDF encontrado para impressao.")
		raise SystemExit(1)

	run_print_job(
		files=files,
		duplex_on=args.duplex == "on",
		grayscale_on=args.grayscale == "on",
		pause_between_files=args.pause_between_files,
	)


if __name__ == "__main__":
	main()
