import os
import shutil
import sys
import time

import yaml
from PyQt5.QtCore import QTimer, QThread, QObject, pyqtSignal, QMutex, Qt, QSize
from PyQt5.QtGui import QIcon, QFont, QColor, QTextCursor, QPalette
from PyQt5.QtWidgets import (QApplication, QTextEdit, QPushButton,
                             QToolTip, QAction, QMainWindow, QMenu, QDialog, QLineEdit, QLabel)

from translators import Translator

PKG_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_DIR = os.path.join(PKG_DIR, 'icon')


def get_icon_path(name):
    return os.path.join(ICON_DIR, name)


class WaitForReleasing(QObject):
    released = pyqtSignal()

    def __init__(self, delay=0.5):
        super().__init__()
        self.delay = delay
        self.start_time = None
        self.mutex = QMutex()
        self._enable = True

    def refresh(self):
        self.mutex.lock()
        self.start_time = time.time()
        self.mutex.unlock()

    def main_thread(self):
        while True:
            self.mutex.lock()
            if self.start_time is not None and time.time() - self.start_time > self.delay:
                self.start_time = None
                if self._enable:
                    self.released.emit()
            self.mutex.unlock()
            time.sleep(0.01)

    def enable(self):
        self.mutex.lock()
        self._enable = True
        self.mutex.unlock()

    def disable(self):
        self.mutex.lock()
        self._enable = False
        self.mutex.unlock()


def sentence_split(string: str):
    modified = string.translate({ord('\n'): ' ', ord('‘'): "'", ord('’'): "'"})
    modified = modified.replace('- ', '').replace('? ', '')
    modified = ''.join(filter(lambda s: s.isprintable(), modified))
    sentences = []

    def _get_first_sentence(_str: str):
        _str = _str.strip()
        for idx, char in enumerate(_str):
            if char in ('.', ':', ';') and (remains := _str[idx + 1:].lstrip()):
                if remains[0].isupper() or remains[0] == '•':
                    return _str[:idx + 1], remains
        else:
            return _str, ''

    while modified:
        sentence, modified = _get_first_sentence(modified)
        sentences.append(sentence)
    return sentences


def get_home_dir():
    if sys.platform == 'win32':
        return os.environ['USERPROFILE']
    elif sys.platform == 'linux' or sys.platform == 'darwin':
        return os.environ['HOME']
    else:
        raise NotImplemented(f'Error! Not this system. {sys.platform}')


class TransConfig:
    USER_CONFIG_PATH = os.path.join(get_home_dir(), '.config', 'trans_gui', 'config.yaml')

    def __init__(self, file=None):
        if file is None:
            file = self.USER_CONFIG_PATH
            if not os.path.exists(file):
                os.makedirs(os.path.dirname(file), exist_ok=True)
                shutil.copy(os.path.join(PKG_DIR, 'config.yaml'), file)

        with open(file, 'r', encoding="utf-8") as f:
            self.config = yaml.safe_load(f.read())

        self.api = self.config['api']['server']
        self._font_cfg = self.config['font_config']

        self._font_family = self._font_cfg['font_family']
        self._font = QFont()
        self._font.setFamily(self._font_family)
        self._font.setPointSize(self.font_size)

        self.ui_font_family = self._font_cfg['ui_font_family']
        self.ui_font_size = self._font_cfg['ui_font_size']
        self.ui_font = QFont()
        self.ui_font.setFamily(self.ui_font_family)
        self.ui_font.setPointSize(self.ui_font_size)

        palette_config = self.config['palette']
        self.ui_pal = QPalette()
        self.ui_pal.setColor(QPalette.Window, QColor(palette_config['background']))

        self.texted_pal = QPalette()
        self.texted_pal.setColor(
            QPalette.Highlight,
            QColor(palette_config['highlight'])
        )
        self.texted_pal.setColor(
            QPalette.HighlightedText,
            QColor(palette_config['highlighted_text'])
        )

        self.tooltip_pal = QPalette()
        self.tooltip_pal.setColor(
            QPalette.Inactive,
            QPalette.ToolTipBase,
            QColor(palette_config['tooltip_base'])
        )
        self.tooltip_pal.setColor(
            QPalette.Inactive,
            QPalette.ToolTipText,
            QColor(palette_config['tooltip_text'])
        )

        style_sheet_config = self.config['style_sheet']
        self.texted_input_style_sheet = ''.join(style_sheet_config['texted_input'])
        self.texted_output_style_sheet = ''.join(style_sheet_config['texted_output'])

    @property
    def font_size(self):
        return self._font_cfg['font_size']

    @font_size.setter
    def font_size(self, value):
        self._font_cfg['font_size'] = value
        self._font.setPointSize(value)
        self.dump()

    @property
    def font(self):
        return self._font

    def dump(self):
        with open(self.USER_CONFIG_PATH, 'w', encoding="utf-8") as f:
            yaml.dump(self.config, f)


class ApiHelper(QDialog):
    size = (200, 135)

    def __init__(self, title: str, label1: str, label2: str, font, palette):
        super().__init__()
        self.setWindowFlags(Qt.WindowCloseButtonHint)
        self.setWindowTitle(title)
        self.setFixedSize(*self.size)
        self.setPalette(palette)

        self.item1, self.item2 = None, None

        self.label1 = QLabel(label1, self)
        self.label1.setFont(font)
        self.label1.move(22, 17)
        self.input1 = QLineEdit(self)
        self.input1.setFixedSize(120, 30)
        self.input1.setFont(font)
        self.input1.move(55, 15)
        self.input1.textChanged.connect(lambda s: setattr(self, 'item1', s))

        self.label2 = QLabel(label2, self)
        self.label2.setFont(font)
        self.label2.move(22, 52)
        self.input2 = QLineEdit(self)
        self.input2.setFixedSize(120, 30)
        self.input2.setFont(font)
        self.input2.move(55, 50)
        self.input2.textChanged.connect(lambda s: setattr(self, 'item2', s))

        self.confirm = QPushButton('确认', self)
        self.confirm.setFont(font)
        self.confirm.move(15, 90)
        self.confirm.released.connect(lambda: super(ApiHelper, self).close())
        self.cancel = QPushButton('取消', self)
        self.cancel.setFont(font)
        self.cancel.move(105, 90)
        self.cancel.released.connect(self.close)

    def get_api_info(self):
        self.exec_()
        return self.item1, self.item2

    def close(self) -> bool:
        self.item1 = self.item2 = None
        return super().close()


class TransGui(QMainWindow):
    def __init__(self, app: QApplication, cfg=TransConfig()):
        super(TransGui, self).__init__()
        self.app = app
        self.cfg = cfg

        self.x, self.y = 0, 0

        self.delay = WaitForReleasing(0.3)
        self.delay_thread = QThread(self)
        self._enabled = True
        self.init_translator(self.cfg.api)
        self.statusBar().showMessage(f'API: {self.translator.api}')
        self.translate_thread = QThread(self)
        self.init_trans()

        self.texted_input = QTextEdit(self)
        self.texted_input.setAcceptRichText(False)
        self.texted_output = QTextEdit(self)

        self.input_buffer = ['' for _ in range(10)]
        self.undo_idx = -2
        self.undo_flag = False

        self.clipboard_record = ''
        self.clipboard = QApplication.clipboard()
        self.clipboard_timer = QTimer()
        self.clipboard_timer.timeout.connect(self.input_clipboard)

        self.menu_bar = self.menuBar()
        self.menu_options = self.menu_bar.addMenu("设置")
        self.cap_clb_action = QAction('自动捕获剪切板', self, checkable=True)
        self.detect_lang_action = QAction('自动检测语言', self, checkable=True)
        self.menu_trans_api = QMenu('翻译来源')
        self.choose_gg_action = QAction('谷歌（免费）', self)
        self.choose_bd_action = QAction('百度', self)
        self.choose_yd_action = QAction('有道', self)
        self.menu_fontsize = self.menu_bar.addAction('字号：13pt')
        self.menu_show_api = self.menu_bar.addAction(f'API: {self.translator.api}')

        self.tool_bar = self.addToolBar('tools')
        self.tool_bar.setIconSize(QSize(25, 18))
        self.grow_font_action = QAction(
            QIcon(get_icon_path('font+.png')), '增大字体', self
        )
        self.grow_font_action.triggered.connect(
            lambda: self.change_fontsize(self.cfg.font.pointSize() + 1)
        )
        self.shrink_font_action = QAction(
            QIcon(get_icon_path('font-.png')), '缩小字体', self
        )
        self.shrink_font_action.triggered.connect(
            lambda: self.change_fontsize(self.cfg.font.pointSize() - 1)
        )
        self.refresh_action = QAction(
            QIcon(get_icon_path('refresh.png')), '刷新', self
        )
        self.refresh_action.triggered.connect(self.refresh_input)
        self.undo_action = QAction(
            QIcon(get_icon_path('undo.png')), '撤销(Ctrl+Z)', self
        )
        self.undo_action.triggered.connect(self.undo)
        self.copy_res_action = QAction(
            QIcon(get_icon_path('copy.png')), '复制翻译结果', self
        )
        self.copy_res_action.triggered.connect(self.on_copy)
        self.screenshot_btn = self.button(
            get_icon_path('shot.png'), 'Select Area', self.screenshot, 'Ctrl+S'
        )
        self.screenshot_btn.setVisible(False)

        self.tool_bar.addAction(self.grow_font_action)
        self.tool_bar.addAction(self.shrink_font_action)
        self.tool_bar.addAction(self.refresh_action)
        self.tool_bar.addAction(self.undo_action)
        self.tool_bar.addAction(self.copy_res_action)

        self.ignore_cursor_movement = False
        self.init_gui()

        self.font_size_changed = False
        self.init_pattern()

        self.show()

    def screenshot(self):
        pass

    def init_translator(self, server: str):
        read_success = False
        if server == 'google':
            read_success = True
        elif f'{server}_api' in self.cfg.config['api']:
            keys = self.cfg.config['api'][f'{server}_api']
            if 'key1' in keys and 'key2' in keys:
                key1, key2 = str(keys['key1']), str(keys['key2'])
                read_success = True
        if not read_success:
            if server == 'baidu':
                self.api_helper = ApiHelper('app_id/app_key', 'id', 'key', self.cfg.ui_font, self.cfg.ui_pal)
            elif server == 'youdao':
                self.api_helper = ApiHelper('app_key/app_secret', 'key', 'sec', self.cfg.ui_font, self.cfg.ui_pal)
            # self.api_helper.setWindowModality(Qt.ApplicationModal)
            x, y = self.geometry().x(), self.geometry().y()
            size_x, size_y = self.api_helper.size
            self.api_helper.move(int(x + (self.x - size_x) / 2), int(y + (self.y - size_y) / 2))
            # self.delay.disable()
            self._enabled = False
            keys = self.api_helper.get_api_info()
            self._enabled = True
            if all(keys):
                self.cfg.config['api']['server'] = server
                self.cfg.config['api'][f'{server}_api'] = {}
                key1 = self.cfg.config['api'][f'{server}_api']['key1'] = keys[0]
                key2 = self.cfg.config['api'][f'{server}_api']['key2'] = keys[1]
                read_success = True
        if read_success:
            self.translator = Translator(server)
            try:
                self.translator.set_api_keys(key1, key2)
            except NameError:
                pass
            self.cfg.config['api']['server'] = server
            self.cfg.dump()
        return read_success

    def select_translator(self, server: str):
        if self.init_translator(server):
            self.menu_show_api.setText(f'API: {self.translator.api}')
            self.translate()

    def undo(self):
        self.texted_input.setPlainText(self.input_buffer[self.undo_idx])
        self.undo_flag = True
        if abs(self.undo_idx) != len(self.input_buffer):
            self.undo_idx -= 1

    def button(self, icon, tip, slot, shortcut=''):
        btn = QPushButton(QIcon(icon), '', self)
        btn.resize(30, 22)
        btn.clicked.connect(slot)
        btn.setToolTip(tip)
        if shortcut:
            btn.setShortcut(shortcut)
        return btn

    def init_trans(self):
        self.translate_thread.started.connect(self.translate)
        self.delay.moveToThread(self.delay_thread)
        self.delay.released.connect(self.on_input_update)
        self.delay_thread.started.connect(self.delay.main_thread)
        self.delay_thread.finished.connect(self.delay_thread.quit)
        self.delay_thread.start()

    def init_pattern(self):
        self.texted_input.setFont(self.cfg.font)
        self.texted_output.setFont(self.cfg.font)

        self.menu_bar.setFont(self.cfg.ui_font)
        self.menu_options.setFont(self.cfg.ui_font)
        self.menu_trans_api.setFont(self.cfg.ui_font)

        self.statusBar().setFont(self.cfg.ui_font)

        self.texted_input.setStyleSheet(self.cfg.texted_input_style_sheet)
        self.texted_output.setStyleSheet(self.cfg.texted_output_style_sheet)

        self.setPalette(self.cfg.ui_pal)
        self.texted_input.setPalette(self.cfg.texted_pal)
        self.texted_output.setPalette(self.cfg.texted_pal)
        QToolTip.setPalette(self.cfg.tooltip_pal)
        QToolTip.setFont(self.cfg.ui_font)

        self.texted_input.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.texted_output.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def init_gui(self):
        self.setGeometry(300, 300, 1040, 600)
        self.setWindowTitle('Translator')
        self.setWindowIcon(QIcon(get_icon_path('icon2.png')))

        self.statusBar().showMessage('ready')
        self.set_capture_clipboard(True)
        self.cap_clb_action.setChecked(True)
        self.cap_clb_action.triggered.connect(self.set_capture_clipboard)
        self.menu_options.addAction(self.cap_clb_action)

        self.detect_lang_action.setChecked(False)
        self.menu_options.addAction(self.detect_lang_action)
        self.menu_options.addMenu(self.menu_trans_api)
        self.menu_trans_api.addAction(self.choose_gg_action)
        self.menu_trans_api.addAction(self.choose_bd_action)
        self.menu_trans_api.addAction(self.choose_yd_action)
        self.choose_bd_action.triggered.connect(lambda: self.select_translator('baidu'))
        self.choose_gg_action.triggered.connect(lambda: self.select_translator('google'))
        self.choose_yd_action.triggered.connect(lambda: self.select_translator('youdao'))

        self.texted_input.textChanged.connect(lambda: self.delay.refresh())
        self.texted_output.setReadOnly(True)
        self.texted_output.cursorPositionChanged.connect(self.text_correspond)

    def refresh_input(self):
        self.texted_input.setPlainText(
            '\n'.join(sentence_split(self.texted_input.toPlainText()))
        )
        self.delay.refresh()

    def on_copy(self):
        string = self.texted_output.toPlainText().replace('\n', '').replace(' ', '')
        self.clipboard.setText(string)
        self.clipboard_record = string

    def change_fontsize(self, font_size):
        font_size = min(max(1, font_size), 48)
        self.cfg.font_size = font_size
        self.font_size_changed = True
        self.menu_fontsize.setText(f'字号：{font_size}pt')
        self.texted_input.setFont(self.cfg.font)
        self.texted_output.setFont(self.cfg.font)

    def text_correspond(self):
        if self.ignore_cursor_movement:
            self.ignore_cursor_movement = False
            return
        row = self.texted_output.textCursor().blockNumber()
        if row == self.texted_output.document().lineCount() - 1:
            cursor_dest = self.texted_input.textCursor()
            cursor_dest.movePosition(QTextCursor.End)
            self.texted_input.setTextCursor(cursor_dest)
            return

        cursor_src_beg = QTextCursor(self.texted_output.document().findBlockByLineNumber(row))
        cursor_src_end = QTextCursor(self.texted_output.document().findBlockByLineNumber(row + 1))
        cursor_src = self.texted_output.textCursor()
        cursor_src.setPosition(cursor_src_beg.anchor(), QTextCursor.MoveAnchor)
        cursor_src.setPosition(cursor_src_end.anchor() - 1, QTextCursor.KeepAnchor)
        self.ignore_cursor_movement = True
        self.texted_output.setTextCursor(cursor_src)
        cursor_dest_beg = QTextCursor(self.texted_input.document().findBlockByLineNumber(row))
        cursor_dest_end = QTextCursor(self.texted_input.document().findBlockByLineNumber(row + 1))
        cursor_dest = self.texted_input.textCursor()
        cursor_dest.setPosition(cursor_dest_beg.anchor(), QTextCursor.MoveAnchor)
        cursor_dest.setPosition(cursor_dest_end.anchor() - 1, QTextCursor.KeepAnchor)
        self.texted_input.setTextCursor(cursor_dest)

    def set_capture_clipboard(self, state):
        if state:
            self.clipboard_timer.start(100)
        else:
            self.clipboard_timer.stop()

    def input_clipboard(self):
        if self._enabled and (string := self.clipboard.text()) != self.clipboard_record:
            self.clipboard_record = string
            if (ss := string.strip()).startswith('$') or ss.count('\\') > 3:
                return
            if ss.count('/') > 3:
                return
            if ss.startswith('x-special/nautilus-clipboard'):
                return
            if string in self.texted_output.toPlainText() or string in self.texted_input.toPlainText():
                return
            sentences = sentence_split(string)
            modified = ''.join(s + '\n' for s in sentences)
            self.texted_input.setPlainText(modified)

    def on_input_update(self):
        self.ignore_cursor_movement = True
        self.translate_thread.quit()
        self.translate_thread.wait()
        self.translate_thread.start()
        if self.undo_flag:
            self.undo_flag = False
            return
        self.undo_idx = -2
        self.input_buffer.append(self.texted_input.toPlainText())
        self.input_buffer.pop(1)

    def translate(self):
        string = self.texted_input.toPlainText()
        self.statusBar().showMessage('translating')
        self.app.processEvents()
        if string and not string.isspace():
            status, translation = self.translator.translate(string)
        else:
            status, translation = '', ''
        self.texted_output.setPlainText(translation + '\n')
        self.statusBar().showMessage('ready' if not status else status)

    def resizeEvent(self, a0) -> None:
        super().resizeEvent(a0)
        self.x, self.y = a0.size().width(), a0.size().height()
        side_w = int(round(self.x * 0.02))
        top_h = max(int(round(self.y * 0.1)), 25) + 10
        box_w = int(round(self.x * 0.48))
        box_h = int(round(self.y * 0.833))
        self.texted_input.move(side_w, top_h)
        self.texted_input.resize(box_w, box_h)
        self.texted_output.move(side_w + box_w, top_h)
        self.texted_output.resize(box_w, box_h)


class TransGuiWithOcr(TransGui):
    def __init__(self, app: QApplication, cfg=TransConfig()):
        super(TransGuiWithOcr, self).__init__(app, cfg)
        self.screenshot_btn.setVisible(True)
        self.ocr_reader = None

    def screenshot(self):
        image_file = '._tmp.png'
        os.system(f'gnome-screenshot -c -a -f {image_file}')
        if image_file in os.listdir():
            if self.ocr_reader is None:
                self.statusBar().showMessage('loading model')
                self.app.processEvents()
                self.ocr_reader = easyocr.Reader(['en'])
            self.statusBar().showMessage('recognising')
            self.app.processEvents()
            result = self.ocr_reader.readtext(image_file)
            os.remove(image_file)
            if result:
                text = ' '.join(text for loc, text, prob in result)
                sentences = sentence_split(text)
                modified = ''.join(s + '\n' for s in sentences)
                self.texted_input.setPlainText(modified)
        else:
            self.statusBar().showMessage('shot cancelled')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    os.chdir(os.path.dirname(__file__))
    use_ocr = False
    if use_ocr:
        import easyocr

        w = TransGuiWithOcr(app)
    else:
        w = TransGui(app)
    sys.exit(app.exec_())
