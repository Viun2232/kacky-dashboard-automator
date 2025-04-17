import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import os
import threading
import sys
from PIL import Image, ImageTk
from bs4 import BeautifulSoup
import json
import configparser
import re
import importlib.util
import shutil
import webbrowser
import locale
import time
import select
import requests
import math
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_PATH = os.path.join(BASE_DIR, "config.ini")
MAP_RECORDS_PATH = os.path.join(BASE_DIR, "map_records.txt")
README_PATH = os.path.join(BASE_DIR, "README.txt")
REQUIREMENTS_PATH = os.path.join(BASE_DIR, "requirements.txt")
FIRST_RUN_FLAG_PATH = os.path.join(BASE_DIR, "first_run.flag")
FRIENDS_PATH = os.path.join(BASE_DIR, "friends.ini")

LOGO_PATH = os.path.join(BASE_DIR, "logo.png")
ICON_PATH = os.path.join(BASE_DIR, "KDA.ico")
LANG_IMG_PATH = os.path.join(BASE_DIR, "lang.png")
STOP_IMG_PATH = os.path.join(BASE_DIR, "stop.png")

# 최초 실행 확인
def check_first_run_setup():
    if os.path.exists("first_run.flag"):
        log_message("first_run")
        check_environment()
        os.remove("first_run.flag")  # 최초 실행 플래그 제거
        log_message("all_components_installed")

def check_environment():
    log_message("start_env_check")

    python_in_path = shutil.which("python") or shutil.which("python3")
    current_python_path = sys.executable

    log_message("current_python", current_python_path=current_python_path)

    if python_in_path:
        log_message("python_in_path", python_in_path=python_in_path)
    else:
        log_message("python_not_found")
        log_message("how_to_fix")
        log_message("fix_step_1")
        log_message("fix_step_2")
        log_message("fix_step_3")
        log_message("fix_step_4")
        log_message(f"   {os.path.dirname(current_python_path)}")
        log_message("fix_reminder")

    req_path = os.path.join(BASE_DIR, "requirements.txt")
    missing = []

    if not os.path.exists(req_path):
        log_message("requirements_missing")
        return

    import_name_map = {
        "beautifulsoup4": "bs4",
        "pillow": "PIL",
        "webdriver-manager": "webdriver_manager"
    }

    with open(req_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            pip_pkg = line.split("==")[0]
            import_name = import_name_map.get(pip_pkg, pip_pkg.replace("-", "_"))
            try:
                importlib.import_module(import_name)
            except ImportError:
                missing.append(line)

    if missing:
        log_message("missing_libraries")
        for m in missing:
            log_message(f" - {m}")
        log_message("installing_missing")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)
            log_message("missing_installed")
        except Exception as e:
            log_message("install_failed", e=e)
    else:
        log_message("all_installed")

    log_message("env_check_complete")

# config.ini 파일 로드
def load_config():
    global current_language, shortcuts
    config = configparser.ConfigParser()

    # 기본값 정의
    default_settings = {
        "pid": "",
        "sheet_id": "",
        "language": "en"
    }

    default_shortcuts = {
        "save": "Ctrl+S",
        "run": "Ctrl+R",
        "quit": "Ctrl+Q"
    }

    default_rank = {
        "total_maps": "526",
        "kacky_color": "positive"
    }

    # config.ini가 없으면 생성
    if not os.path.exists(CONFIG_PATH):
        config["Settings"] = default_settings
        config["Shortcuts"] = default_shortcuts
        config["Rank"] = default_rank
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            config.write(f)

    # config.ini 읽기
    config.read(CONFIG_PATH, encoding="utf-8")

    # Settings 섹션 처리
    if "Settings" not in config:
        config["Settings"] = default_settings
    else:
        for key, value in default_settings.items():
            if key not in config["Settings"] or not config["Settings"][key].strip():
                config["Settings"][key] = value

    # Shortcuts 섹션 처리
    if "Shortcuts" not in config:
        config["Shortcuts"] = default_shortcuts
    else:
        for key, value in default_shortcuts.items():
            if key not in config["Shortcuts"] or not config["Shortcuts"][key].strip():
                config["Shortcuts"][key] = value

    # Rank 섹션 처리
    if "Rank" not in config:
        config["Rank"] = default_rank
    for key, value in default_rank.items():
        if key not in config["Rank"] or not config["Rank"][key].strip():
            config["Rank"][key] = value

    # config 저장
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        config.write(f)

    # 결과 적용
    current_language = config["Settings"]["language"]

    # 단축키 변환
    def to_tk_format(value):
        return value.lower().replace("ctrl+", "<Control-").replace("alt+", "<Alt-").replace("shift+", "<Shift-") + ">"

    shortcuts = {}
    for key in default_shortcuts:
        shortcuts[key] = to_tk_format(config["Shortcuts"][key].strip())

    pid_var.set(config["Settings"]["pid"])
    sheet_id_var.set(config["Settings"]["sheet_id"])

def save_config():
    config = configparser.ConfigParser()

    # 설정 파일이 존재하면 기존 내용 불러오기
    if os.path.exists(CONFIG_PATH):
        config.read(CONFIG_PATH, encoding="utf-8")

    # Settings 섹션이 없다면 생성
    if "Settings" not in config:
        config["Settings"] = {}

    # 기본값 처리 (공백 방지 포함)
    pid = pid_var.get().strip()
    sheet_id = sheet_id_var.get().strip()
    lang = current_language.strip() if current_language else "ko"

    config["Settings"]["pid"] = pid if pid else "0000"
    config["Settings"]["sheet_id"] = sheet_id if sheet_id else "unknown"
    config["Settings"]["language"] = lang

    with open(CONFIG_PATH, "w", encoding="utf-8") as configfile:
        config.write(configfile)

    log_message("config_saved")
    get_username()

def save_language():
    config = configparser.ConfigParser()

    # 설정 파일이 존재하면 읽기
    if os.path.exists(CONFIG_PATH):
        config.read(CONFIG_PATH, encoding="utf-8")

    # Settings 섹션이 없으면 생성
    if "Settings" not in config:
        config["Settings"] = {}

    # 언어 값이 비었을 경우 기본값 설정
    lang = current_language.strip().lower() if current_language else "ko"
    if lang not in ["ko", "en"]:
        lang = "en"  # 허용되지 않은 값은 기본값 사용

    config["Settings"]["language"] = lang

    with open(CONFIG_PATH, "w", encoding="utf-8") as configfile:
        config.write(configfile)

# 현재 언어 상태 변수
current_language = "en"  # 기본값: 영어

def load_language():
    global current_language
    config = configparser.ConfigParser()

    if not os.path.exists(CONFIG_PATH):
        # config.ini가 없을 때 자동 생성
        config["Settings"] = {"language": "en"}
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            config.write(f)
        current_language = "en"
        return

    config.read(CONFIG_PATH, encoding="utf-8")

    # "Settings" 섹션이 없을 경우 생성
    if "Settings" not in config:
        config["Settings"] = {}

    # 언어 값 읽기 (공백 또는 유효하지 않은 값 처리)
    lang_value = config["Settings"].get("language", "").strip().lower()

    if lang_value not in ("ko", "en"):
        # 기본값으로 설정
        lang_value = "en"
        config["Settings"]["language"] = lang_value
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            config.write(f)

    current_language = lang_value

# 프로그램 실행 시 언어 설정 불러오기
load_language()

def load_map_settings():
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_PATH):
        config.read(CONFIG_PATH, encoding="utf-8")
        total_maps = config.getint("Rank", "total_maps", fallback=526)
        kacky_color = config.get("Rank", "kacky_color", fallback="positive").strip().lower()
        if kacky_color not in ["positive", "negative"]:
            kacky_color = "positive"
            config.set("Rank", "kacky_color", "positive")

            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                config.write(f)

        is_positive = kacky_color == "positive"
        return total_maps, is_positive

    return 526, True  # 기본값

def get_rank_and_color(count, total, is_positive=True):
    kacky_positive_colors = ["#aa0000", "#aa0000", "#aa6600", "#aaaa00", "#00aa00"]
    kacky_negative_colors = ["#aa0066", "#aa0066", "#aa3300", "#aa6600", "#ff4400"]

    thresholds = [
        (math.ceil(total * 1.0), "kacky", kacky_positive_colors if is_positive else kacky_negative_colors),
        (math.ceil(total * 0.866666), "gold", "#ffdd00"),
        (math.ceil(total * 0.666666), "silver", "#cccccc"),
        (math.ceil(total * 0.333333), "bronze", "#cc8844"),
        (math.ceil(total * 0.133333), "plastic", "#bbffee"),
    ]

    for threshold, rank_name, color in thresholds:
        if count >= threshold:
            return (rank_name, color)

    return ("norank", "#ffffff")

def get_username():
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_PATH):
        config.read(CONFIG_PATH, encoding="utf-8")
        pid = config.get("Settings", "pid", fallback="")
        sheet_id = config.get("Settings", "sheet_id", fallback="")

        username_display_label.configure(state="normal")
        username_display_label.delete("1.0", tk.END)

        if pid and sheet_id:
            try:
                # ✅ 클리어한 맵 개수 계산
                clear_count = 0
                if os.path.exists(MAP_RECORDS_PATH):
                    with open(MAP_RECORDS_PATH, "r", encoding="utf-8") as file:
                        clear_count = len([line for line in file if line.strip()])

                # ✅ 전체 맵 수 및 색상 가져오기
                total_maps, is_positive = load_map_settings()
                rank_name, rank_color = get_rank_and_color(clear_count, total_maps, is_positive)

                if rank_name == "kacky" and isinstance(rank_color, list):
                    symbols = ["["] + list(str(clear_count)) + ["]", " "]
                    for i, char in enumerate(symbols):
                        color = rank_color[min(i, len(rank_color) - 1)]
                        tag_name = f"rank_{i}"
                        username_display_label.tag_configure(tag_name, foreground=color, font=("Arial", 14, "bold"))
                        username_display_label.insert(tk.END, char, tag_name)
                else:
                    tag_name = f"rank_tag"
                    username_display_label.tag_configure(tag_name, foreground=rank_color, font=("Arial", 14, "bold"))
                    username_display_label.insert(tk.END, f"[{clear_count}] ", tag_name)

                # ✅ 유저 페이지 파싱
                url = f"https://kackiestkacky.com/hunting/editions/players.php?pid={pid}&edition=0"
                response = requests.get(url, timeout=10)
                soup = BeautifulSoup(response.text, "html.parser")
                h4 = soup.find("h4", class_="text-center padding-top")

                if h4:
                    if all(isinstance(child, str) for child in h4.contents):
                        full_text = h4.get_text(strip=True)
                        if "on All Editions" in full_text:
                            clean_name = full_text.split("on All Editions")[0].strip()
                        else:
                            clean_name = full_text.strip()
                        username_display_label.insert(tk.END, clean_name)
                    else:
                        for i, part in enumerate(h4.contents):
                            if isinstance(part, str):
                                if "on All Editions" in part:
                                    break
                                username_display_label.insert(tk.END, part)
                            elif part.name == "span":
                                style = part.get("style", "")
                                color_match = re.search(r"color:(#[0-9a-fA-F]{6})", style)
                                color = color_match.group(1) if color_match else "#000000"
                                weight = "bold" if "font-weight:bold" in style else "normal"
                                slant = "italic" if "font-style:italic" in style else "roman"

                                tag_name = f"color{i}"
                                username_display_label.tag_configure(
                                    tag_name,
                                    foreground=color,
                                    font=("Arial", 14, weight, slant)
                                )
                                username_display_label.insert(tk.END, part.get_text(), tag_name)

                    username_display_label.tag_add("center", "1.0", "end")
                    username_display_label.tag_configure("center", justify="center")
                else:
                    username_display_label.insert(tk.END, "Unknown")
                    username_display_label.tag_add("center", "1.0", "end")
                    username_display_label.tag_configure("center", justify="center")

            except Exception as e:
                username_display_label.insert(tk.END, "Failed to load nickname")
                username_display_label.configure(state="disabled")
        else:
            username_display_label.insert(tk.END, "Not set")

        username_display_label.configure(state="disabled")

def install_requirements():
    """필수 라이브러리를 설치하는 함수 (한글 경로 깨짐 방지)"""
    log_message("installing_libraries")

    requirements_path = os.path.join(BASE_DIR, REQUIREMENTS_PATH)

    if not os.path.exists(requirements_path):
        log_message("file_not_found", file=REQUIREMENTS_PATH)
        return

    try:
        python_exec = shutil.which("python")  # ✅ Python 실행 파일 찾기
        if not python_exec:
            log_message("error_occurred", error="Python 실행 파일을 찾을 수 없습니다.")
            return

        # ✅ OS에 따라 올바른 인코딩 설정 (Windows → CP949, 그 외 UTF-8)
        encoding = "utf-8"
        if os.name == "nt":  # Windows 환경
            encoding = locale.getpreferredencoding()

        process = subprocess.Popen(
            [python_exec, "-m", "pip", "install", "-r", requirements_path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding=encoding, errors="replace",  # ✅ 한글 깨짐 방지
            bufsize=1, universal_newlines=True,  # ✅ 실시간 출력 활성화
            creationflags=subprocess.CREATE_NO_WINDOW  # ✅ 콘솔 창 숨기기
        )

        # stdout과 stderr 실시간 로그 출력
        while True:
            output = process.stdout.readline()
            if output == "" and process.poll() is not None:
                break
            if output:
                log_message("install_output", output=output.strip())

        while True:
            error_output = process.stderr.readline()
            if error_output == "" and process.poll() is not None:
                break
            if error_output:
                log_message("error_occurred", error=error_output.strip())

        process.stdout.close()
        process.stderr.close()
        process.wait()

        log_message("installation_complete")

    except Exception as e:
        log_message("error_occurred", error=str(e))

running_process = None  # 실행 중인 프로세스를 저장할 변수

script_should_stop = False
stopped_logged = False
driver = None

def stop_script():
    def do_stop():
        global driver, script_should_stop, stopped_logged

        script_should_stop = True

        if driver:
            try:
                driver.quit()
            except Exception:
                pass
            driver = None

        if not stopped_logged:
            log_message("script_stopped")
            stopped_logged = True

    threading.Thread(target=do_stop, daemon=True).start()

def check_stop():
    if script_should_stop:
        raise InterruptedError("🛑 The script was interrupted by the user.")

def format_time(record_time):
    """
    기록 시간 형식을 변환하는 함수 (예: 00:12.345 -> 12.345)
    """
    match = re.match(r"(?:0+:)?(\d+\.\d+)", record_time)
    return match.group(1) if match else record_time

def get_maps():
    global script_should_stop, stopped_logged, driver
    check_stop()

    map_data = []
    records = {}

    # ✅ Selenium 실행 및 크롤링 과정 복구
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging", "enable-automation"])
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    chrome_service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

    check_stop()
    if not driver:
        return

    # ✅ 설정 파일 로드
    config_file = "config.ini"
    config = configparser.ConfigParser()
    if os.path.exists(config_file):
        config.read(config_file, encoding="utf-8")
        pid = config.get("Settings", "pid", fallback=None)
        sheet_id = config.get("Settings", "sheet_id", fallback=None)
        log_message("load_complete", pid=pid, sheet_id=sheet_id)
    else:
        log_message("no_settings")
        pid, sheet_id = None, None

    # ✅ 기존 기록 로드
    log_message("load_records")
    record_file = "map_records.txt"
    existing_records = {}

    if os.path.exists(record_file):
        with open(record_file, "r", encoding="utf-8") as file:
            for line in file:
                parts = line.strip().split("\t")
                if len(parts) == 3:
                    existing_records[parts[0]] = (parts[1], parts[2])  # (기록, 랭크)

    # ✅ 맵 UID 수집 시작

    log_message("fetching_map_uids")
    url = f"https://kackiestkacky.com/hunting/editions/players.php?pid={pid}&edition=0"

    try:
        driver.get(url)
        WebDriverWait(driver, 15).until(
            EC.invisibility_of_element((By.CLASS_NAME, "dataTables_empty"))
        )
    
        history_table = driver.find_element(By.ID, "history")
        links = history_table.find_elements(By.CLASS_NAME, "hover-preview")
        ranks = history_table.find_elements(By.XPATH, "//td[3]")

        map_data = []
        for link, rank_cell in zip(links, ranks):

            map_name = link.text.strip()
            map_uid = link.get_attribute("data-uid")
            current_rank = rank_cell.text.strip()
        
            # 기존 기록과 비교하여 갱신된 맵만 저장
            if map_name in existing_records and existing_records[map_name][1] == current_rank and existing_records[map_name][0] != "N/A":
                continue
        
            map_data.append((map_name, map_uid, current_rank))
    
        log_message("map_uid_collected", count=len(map_data))

    except Exception as e:
        pass

    finally:
        if driver:
            driver.quit()
            driver = None

    # ✅ 최고 기록 가져오기
    records = existing_records.copy()
    driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

    for map_name, map_uid, current_rank in map_data:
        check_stop()
        if not driver:
            return

        record_url = f"https://kackiestkacky.com/hunting/editions/maps.php?uid={map_uid}"
        log_message("accessing", url=url)

        check_stop()
        if not driver:
            return

        try:
            driver.get(record_url)
            WebDriverWait(driver, 15).until(
                EC.invisibility_of_element((By.CLASS_NAME, "dataTables_empty"))
            )

            try:
                dropdown = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "maps_length"))
                )
                driver.execute_script("""
                    let dropdown = document.querySelector('select[name="maps_length"]');
                    if (dropdown) {
                        dropdown.value = '-1';
                        dropdown.dispatchEvent(new Event('change'));
                    }
                """)
                log_message("change_filter")
            except Exception:
                log_message("dropdown_not_found")

            rows = driver.find_elements(By.TAG_NAME, "tr")
            best_time = "N/A"

            for row in rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= 3:
                    player_text = cells[1].text.strip()
                    record_time = format_time(cells[2].text.strip())
                
                    if f"pid={pid}" in cells[1].get_attribute("innerHTML"):
                        best_time = record_time
                        log_message("record_updated", map_name=map_name, best_time=best_time, current_rank=current_rank)
                        break

            records[map_name] = (best_time, current_rank)

        except Exception as e:
            log_message("record_not_found", map_name=map_name, error=str(e))

    if driver:
        driver.quit()
        driver = None
    
    check_stop()

    # ✅ 파일 저장
    log_message("record_save")
    with open(record_file, "w", encoding="utf-8") as file:
        for map_name, (best_time, rank) in records.items():
            file.write(f"{map_name}\t{best_time}\t{rank}\n")

    log_message("save_complete")

def check_list():
    global script_should_stop, stopped_logged
    check_stop()

    # config.ini 파일 읽기
    config = configparser.ConfigParser()
    config.read("config.ini")
    sheet_id = config.get("Settings", "sheet_id", fallback="")

    with open("map_records.txt", "r", encoding="utf-8") as file:
        map_records_content = file.read()

    payload = {
        "map_records": map_records_content,
        "sheet_id": sheet_id
    }

    check_stop()

    # GAS 웹 앱 호출
    log_message("send_request")

    if not os.path.exists(MAP_RECORDS_PATH):
        log_message("script_output", output="❌ map_records.txt is missing!")
        return

    with open(MAP_RECORDS_PATH, "r", encoding="utf-8") as file:
        map_records_content = file.read()

    payload = {
        "map_records": map_records_content,
        "sheet_id": sheet_id
    }

    check_stop()

   # 요청 헤더 추가 (Content-Type: application/json)
    headers = {
        "Content-Type": "application/json"
    }

    webhook_url = "https://script.google.com/macros/s/AKfycbxHHq_QxnkQb3MNqxITXIjKxfw16kbuPCxVrXYK5xLSLSd2lh1P2KZZUa7Dx5kBsg/exec"

    response = requests.post(webhook_url, json=payload, headers=headers)  # headers 추가

    check_stop()

    if response.status_code == 200:
        log_message("success", response=response.text)
    else:
        log_message("fail", status_code=response.status_code)
        log_message("response", response_text=response.text)

def run_scripts():
    global script_should_stop, stopped_logged
    script_should_stop = False
    stopped_logged = False

    def execute():
        try:
            check_stop()
            get_maps()
            check_stop()
            check_list()
        except InterruptedError:
            pass
        except Exception as e:
            log_message("unexpected_error", error=str(e))

    threading.Thread(target=execute, daemon=True).start()

# README.txt 열기
def open_readme():
    """README.txt 파일을 메모장에서 실행"""
    if os.path.exists(README_PATH):
        subprocess.Popen(["notepad.exe", README_PATH])
    else:
        messagebox.showerror(
            translations[current_language]["error"],
            translations[current_language]["readme_missing"]
        )

# 구글 시트 열기
def open_google_sheet():
    """Sheet ID 값을 기반으로 구글 시트 링크를 엶"""
    sheet_id = sheet_id_var.get().strip()  # ✅ Sheet ID 입력값 가져오기

    if sheet_id:  # ✅ Sheet ID 값이 있는 경우 → 해당 시트 열기
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit?usp=sharing"
    else:  # ✅ Sheet ID 값이 없는 경우 → 기본 시트 열기
        url = "https://docs.google.com/spreadsheets/d/1G44h9PAHVSKkYwD4ek_v6WpI696QPMAJPo1dMVi1IdM/edit?usp=sharing"

    webbrowser.open(url)  # ✅ 브라우저에서 링크 열기

# 유저 페이지 열기
def open_user_page():
    """PID 값을 기반으로 유저 페이지를 엶"""
    pid = pid_var.get().strip()  # ✅ PID 입력값 가져오기

    if pid:  # ✅ PID 값이 있는 경우 → 유저 페이지 열기
        url = f"https://kackiestkacky.com/hunting/editions/players.php?pid={pid}&edition=0"
    else:  # ✅ PID 값이 없는 경우 → 기본 페이지 열기
        url = "https://kackiestkacky.com/"

    webbrowser.open(url)  # ✅ 웹사이트 열기

# LIS 목록 열기
def open_lis_list():
    url = "https://docs.google.com/document/d/1ce1WhT_5MVHhPd-XX39mr6zHv7RWScGp4mCJ9OuBJWc/edit?usp=sharing"
    webbrowser.open_new_tab(url)

def get_logo():
    return ImageTk.PhotoImage(Image.open(LOGO_PATH))

# 우클릭 복사 기능 함수
def copy_selected_item(listbox):
    selection = listbox.curselection()
    if selection:
        value = listbox.get(selection[0])
        root.clipboard_clear()
        root.clipboard_append(value)
        root.update()

def attach_context_menu(listbox):
    menu = tk.Menu(listbox, tearoff=0)
    menu.add_command(label=message_translations[current_language]["copy"], command=lambda: copy_selected_item(listbox))

    def show_context_menu(event):
        try:
            listbox.selection_clear(0, tk.END)
            listbox.selection_set(listbox.nearest(event.y))
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    listbox.bind("<Button-3>", show_context_menu)

# 친구 리스트 함수
friends_data = []

def open_friend_list():
    global friends_data
    friends_data = load_friends()

    x, y = get_window_position()
    popup = tk.Toplevel(root)
    popup.title(title_translations[current_language]["friend_list"])
    popup.geometry(f"385x214+{x + 0}+{y + 203}")
    popup.transient(root)
    popup.grab_set()
    popup.focus_force()
    popup.lift() 

    # 메인 프레임
    main_frame = ttk.Frame(popup)
    main_frame.pack(fill="both", expand=True, padx=10, pady=10)

    # 왼쪽: 친구 리스트
    left_frame = ttk.Frame(main_frame)
    left_frame.pack(side="left", fill="both", expand=True)

    scrollbar = ttk.Scrollbar(left_frame, orient="vertical")
    friend_listbox = tk.Listbox(left_frame, yscrollcommand=scrollbar.set, height=10, font=("Arial", 11))
    scrollbar.config(command=friend_listbox.yview)
    scrollbar.pack(side="right", fill="y")
    friend_listbox.pack(side="left", fill="both", expand=True)

    attach_context_menu(friend_listbox)

    for idx, friend in enumerate(friends_data):
        name = friend.get("name", f"Friend {idx + 1}")
        count = friend.get("clear_count", "?")
        friend_listbox.insert(tk.END, f"[{count}] {name}")

    # 오른쪽: 버튼들
    right_frame = ttk.Frame(main_frame)
    right_frame.pack(side="right", fill="y", padx=(10, 0))

    def get_selected_friend():
        selection = friend_listbox.curselection()
        if not selection:
            messagebox.showwarning(title_translations[current_language]["notice"], message_translations[current_language]["select_friend"], parent=popup)
            return None
        return friends_data[selection[0]], selection[0]

    ttk.Button(right_frame, text=translations[current_language]["add_friend_btn"], width=10, command=lambda: add_friend(friend_listbox, popup)).pack(pady=5)
    ttk.Button(right_frame, text=translations[current_language]["remove_btn"], width=10, command=lambda: remove_friend(friend_listbox)).pack(pady=(5, 24))
    ttk.Button(right_frame, text=translations[current_language]["compare_btn"], width=10, command=lambda: compare_friend(get_selected_friend()[0]) if get_selected_friend() else None).pack(pady=5)
    ttk.Button(right_frame, text=translations[current_language]["dashboard_btn"], width=10, command=lambda: open_sheet(get_selected_friend()[0]["sheet_id"]) if get_selected_friend() else None).pack(pady=5)
    ttk.Button(right_frame, text=translations[current_language]["userpage_btn"], width=10, command=lambda: open_userpage(get_selected_friend()[0]["pid"]) if get_selected_friend() else None).pack(pady=5)

def load_friends():
    config = configparser.ConfigParser()
    if not os.path.exists(FRIENDS_PATH):
        log_message("script_output", output="❌ friends.ini is missing!")
        return []

    config.read(FRIENDS_PATH, encoding="utf-8")
    friends = []

    log_message("friends_ini_loaded")
    for section in config.sections():
        if section.startswith("friend_") or section.isdigit():  # <- 숫자 PID인 경우 처리
            try:
                friend = {
                    "pid": config.get(section, "pid", fallback=section),
                    "sheet_id": config.get(section, "sheet_id", fallback=""),
                    "name": config.get(section, "name", fallback="Unknown"),
                    "clear_count": config.getint(section, "clear_count", fallback=0),
                    "cleared_map": config.get(section, "cleared_map", fallback="").split(", ")
                }
                friends.append(friend)
                # log_message("script_output", output=f"✅ 친구 로드됨: {friend['name']} (맵 {friend['clear_count']}개)")
            except Exception as e:
                log_message("friend_load_failed", section=section, e=e)

    return friends

# 친구 추가 팝업
def add_friend(listbox=None, parent_popup=None):
    x, y = get_window_position()
    add_window = tk.Toplevel()
    add_window.title(title_translations[current_language]["add_friend"])
    add_window.geometry(f"240x144+{x + 120}+{y + 180}")
    add_window.transient(parent_popup)
    add_window.grab_set()
    add_window.focus_force()
    add_window.lift()

    def confirm_add():
        pid = pid_entry.get().strip()
        sheet_id = sheet_entry.get().strip()

        if not pid:
            messagebox.showwarning(title_translations[current_language]["warning"], message_translations[current_language]["pid_required"], parent=add_window)
            return

        # ✅ 현재 config.ini의 pid와 중복 확인
        config_main = configparser.ConfigParser()
        if os.path.exists("config.ini"):
            config_main.read("config.ini", encoding="utf-8")
            current_pid = config_main.get("Settings", "pid", fallback="")
            if pid == current_pid:
                messagebox.showwarning(title_translations[current_language]["warning"], message_translations[current_language]["already_added"], parent=add_window)
                return

        # ✅ 중복 추가 방지
        config = configparser.ConfigParser()
        if os.path.exists("friends.ini"):
            config.read("friends.ini", encoding="utf-8")
            if pid in config.sections():
                messagebox.showwarning(title_translations[current_language]["warning"], message_translations[current_language]["already_added"], parent=add_window)
                return

        record_path = os.path.join("records", f"{pid}_records.txt")

        # ✅ 이름은 항상 BeautifulSoup으로 가져오기
        name = get_friend_name(pid)
        if not name:
            messagebox.showerror(title_translations[current_language]["error"], message_translations[current_language]["name_fail"], parent=add_window)
            return

        # ✅ 기록 파일이 있으면 개수만 계산, 없으면 셀레니움 실행
        record_path = os.path.join("records", f"{pid}_records.txt")
        if os.path.exists(record_path):
            with open(record_path, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]
                clear_count = len(lines)
        else:
            result = get_friends_map(pid)
            if not result:
                messagebox.showerror(title_translations[current_language]["error"], message_translations[current_language]["record_fail"], parent=add_window)
                return
            name, clear_count, _ = result

        # ✅ friends.ini 저장
        config = configparser.ConfigParser()
        if os.path.exists("friends.ini"):
            config.read("friends.ini", encoding="utf-8")
        config[pid] = {
            "pid": pid,
            "name": name,
            "clear_count": str(clear_count),
            "sheet_id": sheet_id
        }
        with open("friends.ini", "w", encoding="utf-8") as f:
            config.write(f)

        # ✅ listbox에 직접 추가
        if listbox:
            display_text = f"[{clear_count}] {name}"
            listbox.insert(tk.END, display_text)

            # ✅ 내부 리스트도 함께 갱신!
            friends_data.append({
                "pid": pid,
                "sheet_id": sheet_id,
                "name": name,
                "clear_count": clear_count
            })

        messagebox.showinfo(title_translations[current_language]["complete"], message_translations[current_language]["add_success"].format(name=name), parent=add_window)
        add_window.destroy()

    ttk.Label(add_window, text=translations[current_language]["pid_label"]).pack(anchor="w", padx=10, pady=(10, 0))
    pid_entry = ttk.Entry(add_window)
    pid_entry.pack(fill="x", padx=10)
    pid_entry.focus_set()

    ttk.Label(add_window, text=translations[current_language]["sheet_required_label"]).pack(anchor="w", padx=10, pady=(5, 0))
    sheet_entry = ttk.Entry(add_window)
    sheet_entry.pack(fill="x", padx=10)

    ttk.Button(add_window, text=translations[current_language]["confirm_add_btn"], command=confirm_add).pack(pady=10)

#기타 친구 함수
def remove_friend(listbox, popup=None):
    if popup:
        popup.lift()
        popup.focus_force()

    selection = listbox.curselection()
    if not selection:
        messagebox.showwarning(title_translations[current_language]["notice"], message_translations[current_language]["select_to_remove"], parent=popup)
        return
    index = selection[0]

    if index >= len(friends_data):
        messagebox.showerror(title_translations[current_language]["error"], message_translations[current_language]["mismatch_error"], parent=popup)
        return

    if messagebox.askyesno(title_translations[current_language]["warning"], message_translations[current_language]["confirm_remove"], parent=popup):
        pid = friends_data[index]["pid"]

        # friends.ini에서 삭제
        config = configparser.ConfigParser()
        config.read("friends.ini", encoding="utf-8")
        if pid in config.sections():
            config.remove_section(pid)
            with open("friends.ini", "w", encoding="utf-8") as f:
                config.write(f)

        # 내부 리스트와 UI에서 삭제
        friends_data.pop(index)
        listbox.delete(index)

def open_sheet(sheet_id):
    if sheet_id:
        webbrowser.open(f"https://docs.google.com/spreadsheets/d/{sheet_id}")

def open_userpage(pid):
    if pid:
        webbrowser.open(f"https://kackiestkacky.com/hunting/editions/players.php?pid={pid}&edition=0")

def compare_friend(friend, listbox=None, idx=None):
    pid = friend.get("pid")
    if not pid:
        return

    x, y = get_window_position()
    popup = tk.Toplevel(root)
    popup.title(title_translations[current_language]["compare_result"].format(name=friend["name"]))
    popup.geometry(f"600x530+{x + 50}+{y + 50}")

    main_frame = ttk.Frame(popup)
    main_frame.pack(fill="both", expand=True, padx=10, pady=10)

    # 좌측 프레임 (친구 전체 클리어 목록)
    left_frame = ttk.Frame(main_frame)
    left_frame.pack(side="left", fill="both", expand=True)

    # 우측 프레임 (나만/친구만/랭킹 비교)
    right_frame = ttk.Frame(main_frame)
    right_frame.pack(side="right", fill="both", expand=False, padx=(20, 0))

    def create_section(frame, title):
        label = ttk.Label(frame, text=title, font=("Arial", 11, "bold"))
        label.pack(anchor="w")

        listbox_frame = ttk.Frame(frame)
        listbox_frame.pack(fill="both", expand=True, pady=(0, 10))

        scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical")
        listbox = tk.Listbox(listbox_frame, height=6, yscrollcommand=scrollbar.set, font=("Arial", 11))
        scrollbar.config(command=listbox.yview)

        listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        return listbox

    # 왼쪽
    list_friend_clears = create_section(left_frame, translations[current_language]["friend_clears"])
    attach_context_menu(list_friend_clears)

    # 오른쪽
    list_friend_only = create_section(right_frame, translations[current_language]["friend_only"])
    attach_context_menu(list_friend_only)

    list_me_only = create_section(right_frame, translations[current_language]["me_only"])
    attach_context_menu(list_me_only)

    list_rank_lower = create_section(right_frame, translations[current_language]["worse_rank"])
    attach_context_menu(list_rank_lower)

    # 비교 결과 계산 함수
    def compare_with_friend(friend_pid):
        my_records = load_records("map_records.txt")
        friend_records = load_records(f"records/{friend_pid}_records.txt")

        friend_maps = set(friend_records.keys())
        my_maps = set(my_records.keys())

        only_friend = friend_maps - my_maps
        only_me = my_maps - friend_maps
        both = friend_maps & my_maps

        worse_rank = []
        for map_name in both:
            my_rank = parse_rank(my_records[map_name])
            friend_rank = parse_rank(friend_records[map_name])
            if my_rank and friend_rank and my_rank > friend_rank:
                worse_rank.append(map_name)

        return {
            "friend_maps": sorted(friend_maps),
            "only_friend": sorted(only_friend),
            "only_me": sorted(only_me),
            "worse_rank": sorted(worse_rank)
        }

    # 기록 로드
    def load_records(path):
        records = {}
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split("\t")
                    if len(parts) == 3:
                        map_name, _, rank = parts
                    elif len(parts) == 2:
                        map_name, rank = parts
                    else:
                        continue
                    records[map_name] = rank
        return records

    def parse_rank(rank_str):
        try:
            return int(rank_str)
        except:
            return None

    # 리스트박스에 결과 출력
    def display_comparison_results(friend_maps, my_missing, friend_missing, rank_lower):
        def insert_listbox(listbox, items):
            listbox.delete(0, tk.END)
            for item in items:
                listbox.insert(tk.END, item)

        insert_listbox(list_friend_clears, friend_maps)
        insert_listbox(list_friend_only, friend_missing)
        insert_listbox(list_me_only, my_missing)
        insert_listbox(list_rank_lower, rank_lower)

    # 초기 비교 출력
    result = compare_with_friend(pid)
    display_comparison_results(result["friend_maps"], result["only_me"], result["only_friend"], result["worse_rank"])

    # 🔄 갱신 버튼
    def refresh_friend_info(friend, parent_popup):
        pid = friend.get("pid")
        if not pid:
            messagebox.showerror(title_translations[current_language]["error"],
                                 message_translations[current_language]["select_friend"], parent=parent_popup)
            return

        # 이름 + 맵 정보 크롤링
        name_result = get_friend_name(pid)
        result = get_friends_map(pid)

        if not name_result:
            messagebox.showerror(title_translations[current_language]["error"],
                                 message_translations[current_language]["name_fail"], parent=parent_popup)
            return

        if not result or not isinstance(result, tuple):
            messagebox.showerror(title_translations[current_language]["error"],
                                 message_translations[current_language]["record_fail"], parent=parent_popup)
            return

        try:
            name_got, clear_count, _ = result
        except Exception as e:
            messagebox.showerror(title_translations[current_language]["error"],
                                 message_translations[current_language]["friend_parse_failed"].format(error=e), parent=parent_popup)
            return

        # friends.ini 갱신
        config = configparser.ConfigParser()
        config.read("friends.ini", encoding="utf-8")
        if pid in config:
            config[pid]["name"] = name_got
            config[pid]["clear_count"] = str(clear_count)
            with open("friends.ini", "w", encoding="utf-8") as f:
                config.write(f)

        # 친구 목록 UI 갱신
        if listbox and idx is not None:
            updated_display = f"[{clear_count}] {name_got}"
            listbox.delete(idx)
            listbox.insert(idx, updated_display)
            friends_data[idx]["name"] = name_got
            friends_data[idx]["clear_count"] = clear_count

        # 비교 리스트 갱신
        new_result = compare_with_friend(pid)
        display_comparison_results(
            new_result["friend_maps"],
            new_result["only_me"],
            new_result["only_friend"],
            new_result["worse_rank"]
        )

        messagebox.showinfo(title_translations[current_language]["complete"],
                            message_translations[current_language]["friend_refreshed"].format(name=name_got), parent=parent_popup)

    refresh_btn = ttk.Button(popup, text=translations[current_language]["refresh_btn"], command=lambda: refresh_friend_info(friend, popup))
    refresh_btn.pack(pady=(0, 5), anchor="ne", padx=10)

    popup.lift()
    popup.focus_force()
    popup.grab_set()

def get_friends_map(pid):
    try:
        # ✅ 이름은 BeautifulSoup으로 크롤링
        name = "Unknown"
        try:
            url = f"https://kackiestkacky.com/hunting/editions/players.php?pid={pid}&edition=0"
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")
            h4 = soup.find("h4", class_="text-center padding-top")
            if h4:
                full_text = h4.get_text(strip=True)
                name = full_text.split("on All Editions")[0].strip() if "on All Editions" in full_text else full_text.strip()
        except Exception as e:
            log_message("name_crawl_failed", e=e)

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-logging", "enable-automation"])
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

        driver.get(f"https://kackiestkacky.com/hunting/editions/players.php?pid={pid}&edition=0")

        # ✅ 테이블 로드 대기
        WebDriverWait(driver, 15).until(
            EC.invisibility_of_element((By.CLASS_NAME, "dataTables_empty"))
        )

        # ✅ 유저 이름
        h4 = driver.find_element(By.CLASS_NAME, "text-center")
        name = h4.text.split("on All Editions")[0].strip()

        # ✅ 테이블에서 맵 정보 수집
        table = driver.find_element(By.ID, "history")
        rows = table.find_elements(By.TAG_NAME, "tr")
        map_records = []

        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 3:
                map_name = cells[1].text.strip()
                rank = cells[2].text.strip()
                if map_name:
                    map_records.append((map_name, rank))

        clear_count = len(map_records)

        # ✅ 파일로 저장
        os.makedirs("records", exist_ok=True)
        record_path = os.path.join("records", f"{pid}_records.txt")
        with open(record_path, "w", encoding="utf-8") as f:
            for map_name, rank in map_records:
                f.write(f"{map_name}\t{rank}\n")

        driver.quit()
        return name, clear_count, [m[0] for m in map_records]  # 이름, 개수, 맵 이름 리스트

    except Exception as e:
        log_message("crawl_failed", e=e)
        return None

def get_friend_name(pid):
    try:
        url = f"https://kackiestkacky.com/hunting/editions/players.php?pid={pid}&edition=0"
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        h4 = soup.find("h4", class_="text-center padding-top")
        if h4:
            full_text = h4.get_text(strip=True)
            return full_text.split("on All Editions")[0].strip() if "on All Editions" in full_text else full_text.strip()
    except Exception as e:
        log_message("name_crawl_failed", e=e)
    return None

# 다국어 지원 딕셔너리
title_translations = {
    "ko": {
        "friend_list": "친구 목록",
        "add_friend": "친구 추가",
        "compare_result": "{name} - 비교 결과",
        "notice": "알림",
        "warning": "경고",
        "error": "오류",
        "complete": "완료",
    },
    "en": {
        "friend_list": "Friend List",
        "add_friend": "Add Friend",
        "compare_result": "{name} - Comparison Result",
        "notice": "Notice",
        "warning": "Warning",
        "error": "Error",
        "complete": "Complete",
    }
}

translations = {
    "ko": {
        "title": "KK Dashboard Automator",
        "pid_label": "PID:",
        "sheet_label": "Sheet ID:",
        "save_btn": "저장",
        "run_btn": "실행",
        "sheet_page_btn": "대시보드 열기",
        "user_page_btn": "유저 페이지 열기",
        "lis_btn": "LIS 목록 열기",
        "friend_list_btn": "친구 리스트",
        "install_btn": "필수 라이브러리 설치",
        "help_btn": "Help",
        "lang_btn": "언어 변경",
        "add_friend_btn": "친구 추가",
        "remove_btn": "삭제",
        "compare_btn": "비교",
        "dashboard_btn": "대시보드",
        "userpage_btn": "유저페이지",
        "sheet_required_label": "Sheet ID (선택):",
        "confirm_add_btn": "추가",
        "friend_clears": "친구가 클리어한 맵 목록",
        "friend_only": "친구만 클리어한 맵",
        "me_only": "나만 클리어한 맵",
        "worse_rank": "내 랭킹이 더 낮은 공통 맵",
        "refresh_btn": "🔄 이름 + 맵 갱신"
    },
    "en": {
        "title": "KK Dashboard Automator",
        "pid_label": "PID:",
        "sheet_label": "Sheet ID:",
        "save_btn": "Save",
        "run_btn": "Run",
        "sheet_page_btn": "Open Dashboard",
        "user_page_btn": "Open User Page",
        "lis_btn": "Open LIS List",
        "friend_list_btn": "Friend List",
        "install_btn": "Install Requirements",
        "help_btn": "Help",
        "lang_btn": "Change Language",
        "add_friend_btn": "Add Friend",
        "remove_btn": "Remove",
        "compare_btn": "Comparison",
        "dashboard_btn": "Dashboard",
        "userpage_btn": "Userpage",
        "sheet_required_label": "Sheet ID (optional):",
        "confirm_add_btn": "Add",
        "friend_clears": "Maps cleared by friend",
        "friend_only": "Cleared by friend only",
        "me_only": "Cleared by me only",
        "worse_rank": "Common maps where my rank is worse",
        "refresh_btn": "🔄 Refresh Name + Maps"
    }
}

log_translations = {
    "ko": {
        "config_saved": "✅ config.ini 저장 완료!",
        # "config_not_found": "⚠ config.ini 파일이 존재하지 않아 기본값을 생성합니다.",
        # "script_running": "🔄 {script_name} 실행 중...",
        # "script_completed": "✅ {script_name} 실행 완료!",
        "script_stopped": "⛔ 스크립트 실행 중단됨.",
        # "no_script_running": "⚠ 실행 중인 스크립트가 없습니다.",
        "error_occurred": "❌ 오류 발생: {error}",
        "installing_libraries": "📦 필수 라이브러리 설치 중...",
        "installation_complete": "✅ 필수 라이브러리 설치 완료!",
        "file_not_found": "❌ {file} 파일이 존재하지 않습니다.",
        "install_output": "📦 {output}",
        "script_output": "📜 {output}",
        "load_settings": "📥 설정 파일 로드 중...",
        "load_complete": "✅ 설정 로드 완료 - PID: {pid}, Sheet ID: {sheet_id}",
        "no_settings": "⚠ 설정 파일 없음! 기본값 사용",
        "load_records": "📂 기존 기록 로드 중...",
        "fetching_map_uids": "📂 클리어한 맵 UID 수집 중...",
        "accessing": "\n🌍 접근 중: {url}",
        "change_filter": "🔄 필터를 'All'로 변경 완료. 테이블이 다시 로드될 때까지 대기 중...",
        "record_updated": "✅ {map_name} 기록 갱신됨: {best_time} (랭크: {current_rank})",
        "record_save": "📂 갱신된 기록 저장 중...",
        "save_complete": "✅ 모든 기록이 map_records.txt에 저장됨.",
        "map_uid_collected": "🔹 {count}개의 갱신된 클리어 맵 UID 수집 완료.",
        "dropdown_not_found": "⚠️ 드롭다운을 찾지 못함. 기본 10개 기록만 가져옴.",
        "record_not_found": "⚠️ {map_name} 기록 찾기 실패: {error}",
        "send_request": "📤 GAS 웹 앱 호출 중...",
        "success": "✅ GAS 웹 앱 호출 성공: {response}",
        "fail": "❌ GAS 웹 앱 호출 실패. 상태 코드: {status_code}",
        "response": "응답 내용: {response_text}",
        "language_changed": "🌐 언어가 변경되었습니다.",
        "all_components_installed": "✅ 모든 필수 구성 요소가 설치되어 있습니다.",
        "first_run": "🎯 첫 실행입니다. 환경을 점검합니다...",
        "start_env_check": "🧪 환경 점검 시작 (최초 실행)",
        "current_python": "📍 현재 실행 중인 Python 경로: {current_python_path}",
        "python_in_path": "✅ 시스템 PATH에 등록된 python: {python_in_path}",
        "python_not_found": "⚠️ 시스템 PATH에 'python' 명령어가 등록되어 있지 않습니다.",
        "how_to_fix": "💡 해결 방법:",
        "fix_step_1": "1️⃣ 시작 메뉴에서 '시스템 환경 변수 편집'을 검색하여 엽니다.",
        "fix_step_2": "2️⃣ '환경 변수(N)...' 버튼을 클릭합니다.",
        "fix_step_3": "3️⃣ '시스템 변수' 또는 '사용자 변수'에서 'Path'를 선택하고 '편집(E)...'을 클릭합니다.",
        "fix_step_4": "4️⃣ 아래 경로를 새 항목으로 추가한 후 확인을 누릅니다:",
        "fix_reminder": "🔁 변경 후, 프로그램을 다시 실행하거나 컴퓨터를 재시작할 수도 있습니다.",
        "requirements_missing": "❌ requirements.txt 파일이 존재하지 않습니다.",
        "missing_libraries": "⚠️ 누락된 라이브러리 감지됨:",
        "installing_missing": "📦 설치 시도 중...",
        "missing_installed": "✅ 누락된 라이브러리 설치 완료",
        "install_failed": "❌ 라이브러리 설치 실패: {e}",
        "all_installed": "✅ 모든 필수 라이브러리가 설치되어 있습니다.",
        "env_check_complete": "✅ 환경 점검 완료!",
        "map_records_missing": "❌ map_records.txt가 없습니다!",
        "readme_missing": "README.txt 파일이 존재하지 않습니다.",
        "friends_ini_loaded": "📂 friends.ini 로드됨",
        "friend_load_failed": "⚠️ 친구 로딩 실패 ({section}): {e}",
        "name_crawl_failed": "[이름 크롤링 실패] {e}",
        "crawl_failed": "크롤링 실패: {e}"
    },
    "en": {
        "config_saved": "✅ config.ini saved successfully!",
        # "config_not_found": "⚠ config.ini not found. Creating default settings.",
        # "script_running": "🔄 Running {script_name}...",
        # "script_completed": "✅ {script_name} completed!",
        "script_stopped": "⛔ Script execution stopped.",
        # "no_script_running": "⚠ No script is currently running.",
        "error_occurred": "❌ Error occurred: {error}",
        "installing_libraries": "📦 Installing required libraries...",
        "installation_complete": "✅ Library installation complete!",
        "file_not_found": "❌ {file} not found.",
        "install_output": "📦 {output}",
        "script_output": "📜 {output}",
        "load_settings": "📥 Loading settings...",
        "load_complete": "✅ Settings loaded - PID: {pid}, Sheet ID: {sheet_id}",
        "no_settings": "⚠ No settings file found! Using default values.",
        "load_records": "📂 Loading existing records...",
        "fetching_map_uids": "📂 Fetching cleared map UIDs...",
        "accessing": "\n🌍 Accessing: {url}",
        "change_filter": "🔄 Changed filter to 'All'. Waiting for table reload...",
        "record_updated": "✅ {map_name} record updated: {best_time} (Rank: {current_rank})",
        "record_save": "📂 Saving updated records...",
        "save_complete": "✅ All records saved to map_records.txt.",
        "map_uid_collected": "🔹 Collected {count} updated cleared map UIDs.",
        "dropdown_not_found": "⚠️ Could not find dropdown. Fetching only 10 default records.",
        "record_not_found": "⚠️ Failed to find record for {map_name}: {error}",
        "send_request": "📤 Calling GAS Web App...",
        "success": "✅ GAS Web App call successful: {response}",
        "fail": "❌ GAS Web App call failed. Status code: {status_code}",
        "response": "Response content: {response_text}",
        "language_changed": "🌐 The language has been changed.",
        "all_components_installed": "✅ All required components are installed.",
        "first_run": "🎯 First launch detected. Checking environment...",
        "start_env_check": "🧪 Starting environment check (first run)",
        "current_python": "📍 Currently running Python path: {current_python_path}",
        "python_in_path": "✅ Python found in system PATH: {python_in_path}",
        "python_not_found": "⚠️ The 'python' command is not registered in the system PATH.",
        "how_to_fix": "💡 How to fix:",
        "fix_step_1": "1️⃣ Open 'Edit the system environment variables' from the Start menu.",
        "fix_step_2": "2️⃣ Click the 'Environment Variables...' button.",
        "fix_step_3": "3️⃣ In 'System variables' or 'User variables', select 'Path' and click 'Edit...'.",
        "fix_step_4": "4️⃣ Add the path below as a new entry and click OK:",
        "fix_reminder": "🔁 After making changes, restart the program or your computer.",
        "requirements_missing": "❌ requirements.txt file does not exist.",
        "missing_libraries": "⚠️ Missing libraries detected:",
        "installing_missing": "📦 Attempting to install missing libraries...",
        "missing_installed": "✅ Missing libraries installed successfully",
        "install_failed": "❌ Failed to install libraries: {e}",
        "all_installed": "✅ All required libraries are installed.",
        "env_check_complete": "✅ Environment check complete!",
        "map_records_missing": "❌ map_records.txt does not exist!",
        "readme_missing": "README.txt file does not exist.",
        "friends_ini_loaded": "📂 friends.ini loaded",
        "friend_load_failed": "⚠️ Failed to load friend ({section}): {e}",
        "name_crawl_failed": "[Name crawling failed] {e}",
        "crawl_failed": "Crawling failed: {e}"
    }
}

message_translations = {
    "ko": {
        "select_friend": "친구를 선택해주세요.",
        "pid_required": "PID는 필수 항목입니다.",
        "already_added": "이미 추가된 플레이어입니다.",
        "name_fail": "이름을 가져올 수 없습니다.",
        "record_fail": "친구 기록을 가져올 수 없습니다.",
        "add_success": "{name}님이 친구로 추가되었습니다.",
        "select_to_remove": "삭제할 친구를 선택해주세요.",
        "mismatch_error": "내부 데이터와 목록이 일치하지 않습니다.",
        "confirm_remove": "정말로 이 친구를 삭제하시겠습니까?",
        "friend_parse_failed": "친구 데이터 파싱 실패: {error}",
        "friend_refreshed": "{name}님 정보가 갱신되었습니다.",
        "copy": "복사"
    },
    "en": {
        "select_friend": "Please select a friend.",
        "pid_required": "PID is required.",
        "already_added": "This player is already added.",
        "name_fail": "Failed to fetch name.",
        "record_fail": "Failed to fetch friend's records.",
        "add_success": "{name} has been added as a friend.",
        "select_to_remove": "Please select a friend to remove.",
        "mismatch_error": "Internal data does not match list.",
        "confirm_remove": "Are you sure you want to remove this friend?",
        "friend_parse_failed": "Failed to parse friend data: {error}",
        "friend_refreshed": "{name}'s information has been updated.",
        "copy": "Copy"
    }
}

# 현재 언어에 맞게 로그 메시지를 변환하는 함수
def log_translate(key, **kwargs):
    message_template = log_translations.get(current_language, {}).get(key, key)
    return message_template.format(**kwargs)

# 로그 메시지 출력 함수 (변경된 메시지 적용)
def log_message(key, **kwargs):
    translated_message = log_translate(key, **kwargs)
    log_text.insert(tk.END, translated_message + "\n")
    log_text.yview(tk.END)
    root.update_idletasks()

# 언어 변경 함수
def switch_language():
    global current_language
    current_language = "en" if current_language == "ko" else "ko"  # ✅ 한국어 ↔ 영어 전환
    save_language()

    # UI 요소 텍스트 변경
    root.title(translations[current_language]["title"])
    pid_label.config(text=translations[current_language]["pid_label"])
    sheet_label.config(text=translations[current_language]["sheet_label"])
    save_btn.config(text=translations[current_language]["save_btn"])
    install_btn.config(text=translations[current_language]["install_btn"])
    run_btn.config(text=translations[current_language]["run_btn"])
    help_btn.config(text=translations[current_language]["help_btn"])
    user_page_btn.config(text=translations[current_language]["user_page_btn"])
    sheet_page_btn.config(text=translations[current_language]["sheet_page_btn"])
    lis_btn.config(text=translations[current_language]["lis_btn"])
    friend_list_btn.config(text=translations[current_language]["friend_list_btn"])
    lang_btn.config(text=translations[current_language]["lang_btn"])
    lang_btn.config(image=lang_img)
    stop_btn.config(image=stop_img)

    log_message("language_changed")

#  단축키 설정 로드
default_shortcuts = {
    "save": "<Control-s>",
    "run": "<Control-r>",
    "quit": "<Control-q>"
}
shortcuts = default_shortcuts.copy()

def load_shortcuts():
    global shortcuts
    config = configparser.ConfigParser()

    # 설정 파일이 없으면 생성
    if not os.path.exists(CONFIG_PATH):
        config["Shortcuts"] = {k: v.replace("<Control-", "Ctrl+").replace(">", "") for k, v in default_shortcuts.items()}
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            config.write(f)
        return

    config.read(CONFIG_PATH, encoding="utf-8")

    # Shortcuts 섹션이 없으면 생성
    if "Shortcuts" not in config:
        config["Shortcuts"] = {k: v.replace("<Control-", "Ctrl+").replace(">", "") for k, v in default_shortcuts.items()}
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            config.write(f)

    # 변환 함수: Ctrl+S → <Control-s>
    def to_tk_format(value):
        return value.lower().replace("ctrl+", "<Control-").replace("alt+", "<Alt-").replace("shift+", "<Shift-") + ">"

    # 각 단축키 항목 로드
    for key in default_shortcuts:
        raw_value = config["Shortcuts"].get(key, "").strip()
        if raw_value:
            shortcuts[key] = to_tk_format(raw_value)
        else:
            shortcuts[key] = default_shortcuts[key]

def format_shortcut(shortcut):
    return shortcut.replace("<Control-", "Ctrl+").replace("<Alt-", "Alt+").replace("<Shift-", "Shift+").replace(">", "").upper()

# 버튼 위에 마우스를 올리면 툴팁을 표시
class ToolTip:
    def __init__(self, widget, text_func):
        self.widget = widget
        self.text_func = text_func  # 동적으로 툴팁 메시지를 가져옴
        self.tip_window = None

        # 마우스 이벤트 바인딩
        self.widget.bind("<Enter>", self.show_tooltip)  # 마우스가 올라갈 때
        self.widget.bind("<Motion>", self.show_tooltip) # 마우스가 버튼 안에서 움직일 때 (이미지 영역 포함)
        self.widget.bind("<Leave>", self.hide_tooltip)  # 마우스가 벗어날 때

    def show_tooltip(self, event=None):
        """툴팁 창을 생성하고 표시"""
        if self.tip_window or not self.text_func:
            return
        
        text = self.text_func()  # 현재 언어에 맞는 툴팁 메시지 가져오기
        if not text:
            return
        
        # 마우스 좌표 기준으로 위치 조정
        x = event.x_root + 10
        y = event.y_root + 10

        # 툴팁 창 생성
        self.tip_window = tk.Toplevel(self.widget)
        self.tip_window.wm_overrideredirect(True)  # 창 테두리 없애기
        self.tip_window.wm_geometry(f"+{x}+{y}")  # 위치 지정

        # 툴팁 라벨 설정
        label = tk.Label(self.tip_window, text=self.text_func(), background="#ffffe0", relief="solid", borderwidth=1, font=("Arial", 10))
        label.pack(ipadx=5, ipady=2)

    def hide_tooltip(self, event=None):
        """툴팁 창을 숨김"""
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

# 창 크기에 따라 버튼 위치 조정
def position_bottom_left(widget, x_offset=10, y_offset=44):
    def update_position(event=None):
        height = root.winfo_height()
        lang_btn.place(x=10, y=height - 44)
        stop_btn.place(x=50, y=height - 44)
    root.bind("<Configure>", update_position)
    root.after(100, update_position)

# 마지막 창 위치 저장
def save_window_position():
    x = root.winfo_x()
    y = root.winfo_y()
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_PATH):
        config.read(CONFIG_PATH, encoding="utf-8")
    if "Window" not in config:
        config["Window"] = {}
    config["Window"]["x"] = str(x)
    config["Window"]["y"] = str(y)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        config.write(f)

def load_window_position():
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_PATH):
        config.read(CONFIG_PATH, encoding="utf-8")
        if "Window" not in config:
            config["Window"] = {}
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                config.write(f)
            return
        x = config.getint("Window", "x", fallback=None)
        y = config.getint("Window", "y", fallback=None)
        if x and y:
            try:
                root.geometry(f"+{int(x)}+{int(y)}")
            except ValueError:
                pass

def get_window_position():
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_PATH):
        config.read(CONFIG_PATH, encoding="utf-8")
        x = config.getint("Window", "x", fallback=100)
        y = config.getint("Window", "y", fallback=100)
        return x, y
    return 100, 100

def on_exit():
    save_window_position()
    root.destroy()

# GUI 설정
root = tk.Tk()
load_window_position()
load_shortcuts()
root.title(translations[current_language]["title"])
root.geometry("820x417")

# 창 아이콘 변경
if os.path.exists(ICON_PATH):
    root.iconbitmap(ICON_PATH)

# 버튼 아이콘 적용
if os.path.exists(LANG_IMG_PATH):
    lang_img = ImageTk.PhotoImage(Image.open(LANG_IMG_PATH))
else:
    lang_img = None

if os.path.exists(STOP_IMG_PATH):
    stop_img = ImageTk.PhotoImage(Image.open(STOP_IMG_PATH))
else:
    stop_img = None

# frame 선언
top_frame = ttk.Frame(root, padding=10)
top_frame.grid(row=0, column=0, sticky="nw")

# 로고 추가
logo_img = get_logo()
logo_label = tk.Label(top_frame, image=logo_img)
logo_label.grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky="n")

# 닉네임 표시 라벨
username_display_label = tk.Text(
    top_frame,
    height=2,
    width=32,
    wrap="none",
    borderwidth=0,
    highlightthickness=0,
    bg=root.cget("bg"),
    font=("Arial", 14)
)
username_display_label.grid(row=1, column=0, columnspan=2)
username_display_label.grid_propagate(False)
username_display_label.tag_configure("center", justify='center')
username_display_label.tag_add("center", "1.0", "end")

# 설정 입력 필드
pid_var = tk.StringVar()
sheet_id_var = tk.StringVar()

pid_label = ttk.Label(top_frame, text=translations[current_language]["pid_label"])
pid_label.grid(row=2, column=0, sticky="w")

sheet_label = ttk.Label(top_frame, text=translations[current_language]["sheet_label"])
sheet_label.grid(row=3, column=0, sticky="w")

# Entry들과 버튼을 담는 프레임 (한 덩어리로)
input_frame = ttk.Frame(top_frame)
input_frame.grid(row=2, column=1, rowspan=2, sticky="w")

pid_entry = ttk.Entry(input_frame, textvariable=pid_var, width=26)
pid_entry.grid(row=0, column=0, sticky="w", pady=(0, 2))

sheet_entry = ttk.Entry(input_frame, textvariable=sheet_id_var, width=26)
sheet_entry.grid(row=1, column=0, sticky="w")

save_btn = ttk.Button(input_frame, text=translations[current_language]["save_btn"], command=save_config, width=6)
save_btn.grid(row=0, column=1, rowspan=2, padx=(5, 0), sticky="ns")
ToolTip(save_btn, lambda: f"설정 저장 ({format_shortcut(shortcuts['save'])})" if current_language == "ko" else f"Save Settings ({format_shortcut(shortcuts['save'])})")

run_btn = ttk.Button(input_frame, text=translations[current_language]["run_btn"], command=run_scripts, width=6)
run_btn.grid(row=0, column=2, rowspan=2, padx=(5, 0), sticky="ns")
ToolTip(run_btn, lambda: f"스크립트 실행 ({format_shortcut(shortcuts['run'])})" if current_language == "ko" else f"Run Script ({format_shortcut(shortcuts['run'])})")

# UI 요소 생성 (라벨 및 버튼)
sheet_page_btn = ttk.Button(top_frame, text=translations[current_language]["sheet_page_btn"], command=open_google_sheet, width=18)
sheet_page_btn.grid(row=6, column=0, columnspan=2, pady=(15, 5))

user_page_btn = ttk.Button(top_frame, text=translations[current_language]["user_page_btn"], command=open_user_page, width=18)
user_page_btn.grid(row=7, column=0, columnspan=2, pady=5)

lis_btn = ttk.Button(top_frame, text=translations[current_language]["lis_btn"], command=open_lis_list, width=18)
lis_btn.grid(row=8, column=0, columnspan=2, pady=5)

friend_list_btn = ttk.Button(top_frame, text=translations[current_language]["friend_list_btn"], command=open_friend_list, width=18)
friend_list_btn.grid(row=9, column=0, columnspan=2, pady=5)

install_btn = ttk.Button(top_frame, text=translations[current_language]["install_btn"], command=install_requirements, width=18)
install_btn.grid(row=10, column=0, columnspan=2, pady=5)

help_btn = ttk.Button(top_frame, text=translations[current_language]["help_btn"], command=open_readme, width=18)
help_btn.grid(row=11, column=0, columnspan=2, pady=5)

lang_btn = ttk.Button(root, image=lang_img, command=switch_language)
position_bottom_left(lang_btn, x_offset=10, y_offset=44)
ToolTip(lang_btn, lambda: "언어 변경" if current_language == "en" else "Change Language")

stop_btn = ttk.Button(root, image=stop_img, command=stop_script)
position_bottom_left(stop_btn, x_offset=50, y_offset=44)
ToolTip(stop_btn, lambda: "스크립트 중단" if current_language == "ko" else "Stop Script")

# 로그 창
log_text = scrolledtext.ScrolledText(root, height=20, width=70, state="normal")
log_text.grid(row=0, column=1, sticky="nsew", padx=10, pady=5)
root.columnconfigure(1, weight=1)  # 로그 창이 가변적으로 늘어나도록 설정
root.rowconfigure(0, weight=1)

# 첫 실행 상태 확인
check_first_run_setup()

root.protocol("WM_DELETE_WINDOW", on_exit)

# 단축키 설정
load_shortcuts()

root.bind(shortcuts["save"], lambda e: save_config())
root.bind(shortcuts["run"], lambda e: run_scripts())
root.bind(shortcuts["quit"], lambda e: on_exit())

# 설정 로드
load_config()
get_username()

# GUI 실행
root.mainloop()
