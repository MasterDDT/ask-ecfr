# Install UV: https://docs.astral.sh/uv/getting-started/installation/
# Then run with `uv run <this file>`

# /// script
# requires-python = "<3.13"
# dependencies = [
#   "requests<3.0",
#   "beautifulsoup4<5.0",
#   "lxml<6.0",
#   "langchain<0.4",
#   "langchain-openai<0.4",
#   "matplotlib<4.0",
#   "pyqt5<6.0",
# ]
# ///

from bs4 import BeautifulSoup
import requests
import re
from typing import Iterator
import sys
from threading import Thread
import queue
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QComboBox, QProgressDialog, QLabel
from PyQt5.QtCore import Qt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


MAX_THREADS = 1
MAX_REGULATIONS_T0_FETCH = 10

# {'title': 22, 'chapter': 'V'}
class CfrReference:
    def __init__(self, title: str, chapter: str):
        self.title = title
        self.chapter = chapter

# {'starts_on': '2015-12-18', 'ends_on': None, 'type': 'Section', 'hierarchy': {'title': '1', 'subtitle': None, 'chapter': 'I', 'subchapter': 'A', 'part': '2', 'subpart': None, 'subject_group': None, 'section': '2.4', 'appendix': None}, 'hierarchy_headings': {'title': 'Title 1', 'subtitle': None, 'chapter': ' Chapter I', 'subchapter': 'Subchapter A', 'part': 'Part 2', 'subpart': None, 'subject_group': None, 'section': '§ 2.4', 'appendix': None}, 'headings': {'title': 'General Provisions', 'subtitle': None, 'chapter': 'Administrative Committee of the Federal Register', 'subchapter': 'General', 'part': 'General Information', 'subpart': None, 'subject_group': None, 'section': 'General authority of Director.', 'appendix': None}, 'full_text_excerpt': None, 'score': 0.047082312, 'structure_index': 10005, 'reserved': False, 'removed': False, 'change_types': ['effective', 'initial']}
class RegulationReference:
    def __init__(self, body: dict):
        self.base_url = "https://www.ecfr.gov/api"
        # TODO: need body['hierarchy_headings']?
        self.date = body['starts_on']
        self.type = body['type']
        self.title = body['hierarchy']['title']
        self.subtitle = body['hierarchy'].get('subtitle', None)
        self.chapter = body['hierarchy'].get('chapter', None)
        self.subchapter = body['hierarchy'].get('subchapter', None)
        self.part = body['hierarchy'].get('part', None)
        self.subpart = body['hierarchy'].get('subpart', None)
        self.subject_group = body['hierarchy'].get('subject_group', None)
        self.section = body['hierarchy'].get('section', None)
        self.appendix = body['hierarchy'].get('appendix', None)
        self.content = None
    def get_content(self) -> str:
        if self.content is not None:
            return self.content
        # curl -X GET "https://www.ecfr.gov/api/versioner/v1/full/2024-09-30/title-7.xml?subtitle=B&chapter=L"
        url = f"{self.base_url}/versioner/v1/full/{self.date}/title-{self.title}.xml"
        params = {}
        if self.subtitle:         
            params['subtitle'] = self.subtitle
        if self.chapter:
            params['chapter'] = self.chapter
        if self.subchapter:       
            params['subchapter'] = self.subchapter
        if self.part:
            params['part'] = self.part
        if self.subpart:
            params['subpart'] = self.subpart
        if self.section:
            params['section'] = self.section
        if self.appendix:
            params['appendix'] = self.appendix
        response = requests.get(url, params=params)
        if response.status_code == 200:
            self.content = BeautifulSoup(response.text, features='xml').get_text()
            return self.content
        else:
            print(f"Failed to get content for {self.display_name()}: {response}")
            return ""
    def get_words(self) -> list[str]:
        return re.findall(r'\w+', self.get_content().lower())
    def get_complexity(self) -> int: 
        if os.environ.get("OPENAI_API_KEY") is None:
            return 0
        llm = ChatOpenAI(model="o3-mini")
        try:
            response = llm.invoke(f"""
                Analyze this government regulation and determine if it is clear and easy for an average American adult to understand.
                Consider things like sentence structure, vocabulary, and complexity. 
                Return 1 if its not clear, -1 if it is, or 0 if you cannot determine.
                Return only one of those values: 1, -1, or 0.                
                Here is the regulation:\n\n{self.get_content()}
            """)
        except Exception as e:
            # TODO: catch rate limit errors and backoff
            print(f"Ignoring LLM error {e}")
            return 0
        stripped_resp = response.text().strip()
        if stripped_resp == "1":
            return 1
        elif stripped_resp == "-1":
            return -1
        else:
            return 0
    def get_spending(self) -> int: 
        if os.environ.get("OPENAI_API_KEY") is None:
            return 0
        llm = ChatOpenAI(model="o3-mini")
        try:
            response = llm.invoke(f"""
                Analyze this government regulation and determine if it involves spending money.
                Consider things like whether it involves direct budget, headcount, or setting aside funds. 
                Return 1 if it involves spending, -1 if it does not, or 0 if you cannot determine.
                Return only one of those values: 1, -1, or 0.                
                Here is the regulation:\n\n{self.get_content()}
            """)
        except Exception as e:
            # TODO: catch rate limit errors and backoff
            print(f"Ignoring LLM error {e}")
            return 0
        stripped_resp = response.text().strip()
        if stripped_resp == "1":
            return 1
        elif stripped_resp == "-1":
            return -1
        else:
            return 0
    def display_name(self) -> str:
        parts = [
            self.date,
            self.title,
            self.subtitle,
            self.chapter,
            self.subchapter,
            self.part,
            self.subpart,
            self.section,
            self.appendix
        ]
        return "/".join([p or '_' for p in parts])

# {'name': 'United States Agency for Global Media', 'short_name': 'USAGM', 'display_name': 'United States Agency for Global Media', 'sortable_name': 'Agency for Global Media, United States', 'slug': 'united-states-agency-for-global-media', 'children': [], 'cfr_references': [{'title': 22, 'chapter': 'V'}, {'title': 48, 'chapter': '19'}]}
class Agency:
    def __init__(self, body):
        self.base_url = "https://www.ecfr.gov/api"
        self.name = body['name']
        self.slug = body['slug']
        self.short_name = body['short_name']
        self.display_name = body['display_name']
        self.sortable_name = body['sortable_name']
        self.cfr_references = []
        for cfr in body['cfr_references']:
            self.cfr_references.append(CfrReference(cfr['title'], cfr.get('chapter', None)))
        self.children = []
        for child in body.get('children', []):
            self.children.append(Agency(child))
    def get_regs(self) -> Iterator[RegulationReference]:
        # curl -X GET "https://www.ecfr.gov/api/search/v1/results?agency_slugs%5B%5D=agriculture-department&per_page=20&page=1&order=relevance&paginate_by=results"
        url = f"{self.base_url}/search/v1/results"
        page = 1
        while True:
            params = {
                "agency_slugs[]": self.slug,
                "per_page": 100,
                "page": page,
                "order": "relevance",
                "paginate_by": "results",
            }
            response = requests.get(url, params=params).json()
            results = response.get('results', [])
            if len(results) == 0:
                break
            else:
                page += 1
                for reg_res in results:
                    yield RegulationReference(reg_res)

class RegStat:
    def __init__(self, total_words: int, complexity_score: int, spending_score: int):
        self.total_words = total_words
        self.complexity_score = complexity_score
        self.spending_score = spending_score

class AgencyStat:
    def __init__(self, ag: Agency, reg_stats: list[RegStat]):
        self.agency = ag
        self.reg_stats = reg_stats
    def complex_ratios(self) -> list[float]:
        if len(self.reg_stats) == 0:
            return [0.0, 0.0, 1.0]
        complex = sum([1 for i in self.reg_stats if i.complexity_score == 1]) / len(self.reg_stats)
        not_complex = sum([1 for i in self.reg_stats if i.complexity_score == -1]) / len(self.reg_stats)
        return [complex, not_complex, 1.0 - complex - not_complex]
    def spending_ratios(self) -> list[float]:
        if len(self.reg_stats) == 0:
            return [0.0, 0.0, 1.0]
        spending = sum([1 for i in self.reg_stats if i.spending_score == 1]) / len(self.reg_stats)
        not_spending = sum([1 for i in self.reg_stats if i.spending_score == -1]) / len(self.reg_stats)
        return [spending, not_spending, 1.0 - spending - not_spending]
    def total_word_count(self) -> int:
        return sum([i.total_words for i in self.reg_stats])

class EcfrAPI:
    def __init__(self):
        self.base_url = "https://www.ecfr.gov/api"
    def get_agencies(self) -> Iterator[Agency]:
        # curl -X GET "https://www.ecfr.gov/api/admin/v1/agencies.json"
        url = f"{self.base_url}/admin/v1/agencies.json"
        response = requests.get(url).json()
        for ag in response['agencies']:
            yield Agency(ag)
    # TODO: remove this regs parameter and bump max workers
    def get_stats(self, agency_sort_name: str) -> AgencyStat:
        ag = [a for a in self.get_agencies() if a.sortable_name == agency_sort_name][0]
        result_queue = queue.Queue()
        task_queue = queue.Queue()
        all_regs = list(ag.get_regs())
        print(f"Total regs for {ag.display_name}: {len(all_regs)}, limiting to {MAX_REGULATIONS_T0_FETCH}")
        for reg in all_regs[:MAX_REGULATIONS_T0_FETCH]:
            task_queue.put(reg)
        def worker():
            while not task_queue.empty():
                reg = task_queue.get()
                reg_stat = RegStat(len(reg.get_words()), reg.get_complexity(), reg.get_spending())
                print(f"{reg.display_name()} has {reg_stat.complexity_score} complex and {reg_stat.spending_score} spending and {reg_stat.total_words} total words")
                result_queue.put(reg_stat)
        threads = []
        for _ in range(MAX_THREADS):
            thread = Thread(target=worker)
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()
        reg_stats = []
        while not result_queue.empty():
            reg_stats.append(result_queue.get())
        return AgencyStat(ag, reg_stats)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.api = EcfrAPI()
        self.setWindowTitle("Ask ECFR")
        self.setGeometry(100, 100, 800, 600)

        # Main widget and layout
        self.main_widget = QWidget(self)
        self.setCentralWidget(self.main_widget)
        self.layout = QVBoxLayout(self.main_widget)

        # Dropdown
        self.label = QLabel("Pick one", self)
        self.layout.addWidget(self.label)
        self.dropdown = QComboBox(self)
        self.dropdown.addItems([a.sortable_name for a in self.api.get_agencies()])
        self.dropdown.currentTextChanged.connect(self.on_dropdown_change)
        self.layout.addWidget(self.dropdown)

        # reasonable pie
        self.reasonable_figure = plt.Figure()
        self.reasonable_canvas = FigureCanvas(self.reasonable_figure)
        self.layout.addWidget(self.reasonable_canvas)

        # spending pie
        self.spending_figure = plt.Figure()
        self.spending_canvas = FigureCanvas(self.spending_figure)
        self.layout.addWidget(self.spending_canvas)

        # Word count label
        self.word_label = QLabel("", self)
        self.layout.addWidget(self.word_label)

    def on_dropdown_change(self, agency_sort_name: str):
        # Show loading dialog
        loading = QProgressDialog("Loading...", None, 0, 0, self)
        loading.setWindowModality(Qt.WindowModal)
        loading.setCancelButton(None)  # No cancel button
        loading.show()
        QApplication.processEvents()  # Ensure dialog appears immediately

        stats = self.api.get_stats(agency_sort_name)

        # Hide loading dialog and update chart
        loading.close()
        self.update_chart(stats)

    def update_chart(self, stats: AgencyStat):
        complex_ratios = stats.complex_ratios()
        complex_data = {}
        if complex_ratios[0] > 0.0:
            complex_data['complex'] = complex_ratios[0]
        if complex_ratios[1] > 0.0:
            complex_data['not complex'] = complex_ratios[1] 
        if complex_ratios[2] > 0.0:
            complex_data['unknown'] = complex_ratios[2]

        spending_ratios = stats.spending_ratios()
        spending_data = {}
        if spending_ratios[0] > 0.0:
            spending_data['spending'] = spending_ratios[0]
        if spending_ratios[1] > 0.0:
            spending_data['not spending'] = spending_ratios[1]
        if spending_ratios[2] > 0.0:
            spending_data['unknown'] = spending_ratios[2]

        # clear figures
        self.reasonable_figure.clear()
        self.spending_figure.clear()

        # reasonable pie
        reasonble_ax = self.reasonable_figure.add_subplot(111)
        values = list(complex_data.values())
        labels = list(complex_data.keys())
        reasonble_ax.pie(values, labels=labels, autopct='%1.1f%%')
        reasonble_ax.axis('equal')  # Equal aspect ratio ensures pie is circular
        reasonble_ax.set_title("Percentage of Complex Regulations")

        # spending pie
        spending_ax = self.spending_figure.add_subplot(111)
        values = list(spending_data.values())
        labels = list(spending_data.keys())
        spending_ax.pie(values, labels=labels, autopct='%1.1f%%')
        spending_ax.axis('equal')  # Equal aspect ratio ensures pie is circular
        spending_ax.set_title("Percentage of Regulations Involving Spending")

        # Update word count label
        self.word_label.setText(f"""
            Total regulations: {len(stats.reg_stats)}
            Total word count: {stats.total_word_count()}
        """)

        # Refresh canvases
        self.reasonable_canvas.draw()
        self.spending_canvas.draw()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
