import sys
import cv2
import json
import time
import os
import os.path
import pygame
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QSlider,
    QInputDialog, QMessageBox, QScrollArea, QFrame, QDialog, QPushButton, QComboBox, QFileDialog
)
from PyQt5.QtGui import QPalette, QColor, QFont, QIcon
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QRect, QEasingCurve, QSize

class CustomTitleBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.initUI()

    def initUI(self):
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.Background, QColor(0, 0, 0))
        self.setPalette(palette)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.titleLabel = QLabel(self.parent.windowTitle())
        self.titleLabel.setFont(QFont('Thintel', 48))
        self.titleLabel.setStyleSheet('color: green; background-color: black; padding: 10px;')
        layout.addWidget(self.titleLabel, alignment=Qt.AlignLeft)

        self.closeButton = QPushButton("✖")
        self.closeButton.setFont(QFont('Thintel', 55))
        self.closeButton.setStyleSheet('color: green; background-color: black; border: none; padding: 10px;')
        self.closeButton.clicked.connect(self.parent.close)
        layout.addWidget(self.closeButton, alignment=Qt.AlignRight)

        self.titleLabel.setMinimumWidth(450)
        self.titleLabel.setMinimumHeight(80)
        self.titleLabel.setMaximumHeight(80)

        self.setLayout(layout)
        self.setWindowTitle(self.parent.windowTitle())

    def setWindowTitle(self, title):
        self.titleLabel.setText(title)

class CustomDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setStyleSheet("background-color: black; color: green; border: 2px solid green;")

        self.titleBar = CustomTitleBar(self)
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.titleBar)
        self.setLayout(self.layout)

    def setWindowTitle(self, title):
        super().setWindowTitle(title)
        self.titleBar.setWindowTitle(title)

class MusicSelectionDialog(CustomDialog):
    def __init__(self, parent, volume):
        super().__init__(parent)
        self.setWindowTitle("Выбор музыки")
        self.setGeometry(300, 300, 600, 400)

        layout = QVBoxLayout()

        self.label = QLabel("Выберите музыку для воспроизведения:")
        self.label.setFont(QFont('Thintel', 22))
        self.label.setStyleSheet('color: green; background-color: black; padding: 10px;')
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        self.comboBox = QComboBox()
        self.comboBox.setFont(QFont('Thintel', 22))
        self.comboBox.setStyleSheet('color: green; background-color: black; border: 2px solid green; padding: 10px;')
        layout.addWidget(self.comboBox)

        self.volumeSlider = QSlider(Qt.Horizontal)
        self.volumeSlider.setMinimum(0)
        self.volumeSlider.setMaximum(100)
        self.volume = volume
        self.volumeSlider.setValue(self.volume)
        self.volumeSlider.setStyleSheet(
            '''
            QSlider::groove:horizontal {
                border: 0px solid green;
                height: 10px;
                margin: 0px;
                background: black;
            }

            QSlider::handle:horizontal {
                background: black;
                border: 2px solid green;
                width: 20px;
                height: 20px;
                margin: -5px 0px;
                border-radius: 0px;
            }
            '''
        )
        layout.addWidget(self.volumeSlider)

        self.okButton = QPushButton("OK")
        self.okButton.setFont(QFont('Thintel', 22))
        self.okButton.setStyleSheet('color: green; background-color: black; border: 2px solid green; padding: 10px;')
        self.okButton.clicked.connect(self.accept)
        layout.addWidget(self.okButton)

        self.music_files = []  
        self.loadMusicFromFolder(r"Music")

        self.layout.addLayout(layout)
        self.adjustSize()        

    def loadMusicFromFolder(self, folder_path):
        for file in os.listdir(folder_path):
            if file.endswith(('.mp3', '.wav')):
                full_path = os.path.join(folder_path, file)
                self.music_files.append((full_path, file))  
                self.comboBox.addItem(file.replace(".mp3", "").replace(".wav", "").replace("_", " "))  

    def getSelectedMusic(self):
        index = self.comboBox.currentIndex()
        if index >= 0:
            return self.music_files[index][0]  
        else:
            return None

    def getVolume(self):
        self.volume = self.volumeSlider.value()
        return self.volume 

class SaveLoadDialog(CustomDialog):
    def __init__(self, parent, title, mode):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setGeometry(300, 300, 600, 300)

        self.mode = mode
        self.selected_slot = None

        layout = QVBoxLayout()

        self.button1 = self.createSlotButton("Слот 1", 1)
        layout.addWidget(self.button1)

        self.button2 = self.createSlotButton("Слот 2", 2)
        layout.addWidget(self.button2)

        self.button3 = self.createSlotButton("Слот 3", 3)
        layout.addWidget(self.button3)

        self.layout.addLayout(layout)
        self.adjustSize()

    def createSlotButton(self, text, slot_number):
        button = QPushButton(text)
        button.setFont(QFont('Thintel', 22))
        button.setStyleSheet('color: green; background-color: black; border: 2px solid green; padding: 10px;')
        button.clicked.connect(lambda: self.selectSlot(slot_number))
        return button

    def selectSlot(self, slot):
        self.selected_slot = slot
        self.accept()

    def getSelectedSlot(self):
        return self.selected_slot


class Quest:
    def __init__(self, title, description, on_completion=None):
        self.title = title
        self.description = description
        self.completed = False
        self.on_completion = on_completion

    def complete(self):
        self.completed = True
        if self.on_completion:
            self.on_completion()

class Item:
    def __init__(self, name, description):
        self.name = name
        self.description = description

class Node:
    def __init__(self, id, text, options=None):
        self.id = id
        self.text = text
        self.options = options or []
        

class RetroGameInterface(QWidget):
    commandEntered = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        pygame.mixer.init()
        self.initUI()
        self.current_node = None
        self.inventory = []
        self.quests = []
        self.sound_effects = {
            'typing': 'typing.wav',
            'menu_selection': 'menu_selection.wav',
            'transition': 'transition.wav'
        }
        self.normal_typing_speed = 0.03
        self.current_typing_speed = 0.03
        self.fast_typing_speed = 0.00001
        self.volume = 70
        self.background_music = None
        self.current_background_music = None
        self.loadGameData()
        self.showMainMenu()
    
    def exitGame(self):
        self.stopBackgroundMusic()
        self.playSoundEffect('transition')
        self.printText("\n\nExiting...\n\n")
        time.sleep(2)
        sys.exit()
    
    def selectMusic(self):
        dialog = MusicSelectionDialog(self, self.volume)
        self.volume = dialog.getVolume()
        print(self.volume)
        if dialog.exec_() == QDialog.Accepted:
            selected_music = dialog.getSelectedMusic()
            if selected_music:
                self.playBackgroundMusic(selected_music)
                self.volume = dialog.getVolume()
                self.setMusicVolume(self.volume)

    def setMusicVolume(self, volume):
        self.volume = volume
        pygame.mixer.music.set_volume(self.volume / 100)
    
    def playBackgroundMusic(self, music_file):
        self.setMusicVolume(self.volume)
        print(self.current_background_music, music_file)
        if self.current_background_music != music_file:
            if self.current_background_music:
                pygame.mixer.music.stop()
            pygame.mixer.music.load(music_file)
            pygame.mixer.music.play(-1)
            self.current_background_music = music_file

    def closeEvent(self, event):
        self.stopBackgroundMusic()
        event.accept()

    def stopBackgroundMusic(self):
        if self.current_background_music:
            pygame.mixer.music.stop()
            self.current_background_music = None

    def setupCommands(self):
        self.commands = {
            "начать": self.startGame,
            "варианты": self.showOptions,
            "задания": self.showQuests,
            "создатели": self.showCredits,
            "выход": self.exitGame,
            "инвентарь": self.showInventory,
            "сохранение": self.selectSaveSlot,
            "загрузка": self.selectLoadSlot,
            "показать": self.showAsciiArt,
            "экран": self.toggleFullScreen,
            "музыка": self.selectMusic,
            "m": self.selectMusic
        }

    def initUI(self):
        self.setWindowTitle('Retro Game Interface')
        self.setGeometry(100, 100, 800, 600)
        self.setupBackground()

        mainLayout = QVBoxLayout()
        self.setupDisplay(mainLayout)
        self.setupInputField(mainLayout)
        self.setLayout(mainLayout)

        self.setupTimer()
        self.setupCommands()

    def setupBackground(self):
        palette = QPalette()
        palette.setColor(QPalette.Background, QColor(0, 0, 0))
        self.setAutoFillBackground(True)
        self.setPalette(palette)

    def setupDisplay(self, layout):
        self.scrollArea = QScrollArea()
        self.scrollArea.setFrameShape(QFrame.NoFrame)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setStyleSheet('background-color: black;')
        
        self.display = QLabel()
        self.display.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.display.setFont(QFont('Thintel', 22))
        self.display.setStyleSheet('color: green; background-color: black; padding: 20px;')
        self.display.setWordWrap(True)
        self.display.setTextInteractionFlags(Qt.TextSelectableByMouse)
    
        self.scrollArea.setWidget(self.display)
        layout.addWidget(self.scrollArea)


    def setupInputField(self, layout):
        self.inputField = QLineEdit()
        self.inputField.setFont(QFont('Thintel', 22))
        self.inputField.setStyleSheet('color: green; background-color: black; border: 2px solid green; padding: 10px;')
        self.inputField.returnPressed.connect(self.processInput)
        layout.addWidget(self.inputField)

    def setupTimer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(50)

    def showMainMenu(self):
        prev_font = self.display.font()
        self.display.setFont(QFont('Thintel', 72))
        self.printText("Тени Ночного Города", fade_in=True)
        self.display.setFont(prev_font)
        self.updateDisplayText(f"\n\n--- Главное меню ---\n")
        self.printText("\n1. Начать игру")
        self.printText("\n2. Загрузить игру")
        self.printText("\n3. Создатели")
        self.printText("\n4. Выход\n")
    
    def toggleFullScreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def printText(self, text, fade_in=False):
        if fade_in:
            self.fadeInText(text)
        else:
            for char in text:
                self.display.setText(self.display.text() + char)
                QApplication.processEvents()
                time.sleep(self.current_typing_speed)
            self.display.setText(self.display.text() + '\n')
            self.scrollArea.verticalScrollBar().setValue(self.scrollArea.verticalScrollBar().maximum())
        self.current_typing_speed = self.normal_typing_speed
    
    def updateDisplayText(self, text):
        current_text = ""
        for char in text:
            current_text += char
            self.display.setText(current_text)
            QApplication.processEvents()
            time.sleep(self.current_typing_speed)
        self.scrollArea.verticalScrollBar().setValue(self.scrollArea.verticalScrollBar().maximum())
        self.current_typing_speed = self.normal_typing_speed


    def fadeInText(self, text):
        self.display.setText(text)
        QApplication.processEvents()
        self.fadeInColor(text)

    def fadeInColor(self, char):
        label_text = self.display.text()
        label_text = label_text.replace(" ", "-")
        for i in range(256):
            color = QColor(0, i, 0)
            self.display.setStyleSheet(f'color: {color.name()}; background-color: black; padding: 20px;')
            QApplication.processEvents()
            time.sleep(self.current_typing_speed)
        label_text = label_text.replace("-", " ")
        self.display.setText(label_text)
        self.current_typing_speed = self.normal_typing_speed

    def startGame(self):
        self.playSoundEffect('transition')
        self.current_node = self.nodes[0]
        self.updateDisplayText("\n\n" + self.current_node.text + "\n\n")
        self.showOptions()

    def showOptions(self):
        self.playSoundEffect('typing')
        self.printText("\n\nДоступные опции:\n")
        for idx, option in enumerate(self.current_node.options, 1):
            if self.checkOptionRequirements(option):
                requirements = self.getOptionRequirementsText(option)
                self.printText(f"\n{idx}. {option['text']} {requirements}\n")
        self.printText("\n")

    def getOptionRequirementsText(self, option):
        requirements = []
        if "required_items" in option:
            for item in option["required_items"]:
                requirements.append(f"[{item}]")
        if "required_quests" in option:
            for quest in option["required_quests"]:
                requirements.append(f"[{quest}]")
        return " ".join(requirements)

    def checkOptionRequirements(self, option):
        if "required_items" in option:
            for item in option["required_items"]:
                if not self.hasItem(item):
                    return False
        if "required_quests" in option:
            for quest in option["required_quests"]:
                if not self.hasQuest(quest):
                    return False
        return True

    def hasItem(self, item_name):
        return any(item.name == item_name for item in self.inventory)

    def hasQuest(self, quest_title):
        return any(quest.title == quest_title for quest in self.quests)

    def showQuests(self):
        self.playSoundEffect('typing')
        self.printText("\n\nДоступные задания:\n")
        for quest in self.quests:
            self.printText(f"\n- {quest.title}: {quest.description}\n")
        self.printText("\n")

    def showCredits(self):
        self.playSoundEffect('transition')
        self.updateDisplayText("\n\n--- Создатели ---\n\nDefensorem\n\n")

    def showInventory(self):
        self.playSoundEffect('typing')
        self.printText("\n\nИнвентарь:\n")
        for item in self.inventory:
            self.printText(f"\n- {item.name}: {item.description}")
        self.printText("\n")

    def processInput(self):
        command = self.inputField.text().strip().lower()
        self.inputField.clear()

        if command in self.commands:
            self.playSoundEffect('menu_selection')
            self.commands[command]()
        elif command.isdigit():
            option_index = int(command) - 1

            # If we're at the main menu
            if self.current_node is None:
                if option_index == 0:
                    self.startGame()
                elif option_index == 1:
                    self.selectLoadSlot()
                elif option_index == 2:
                    self.showCredits()
                elif option_index == 3:
                    self.exitGame()
                else:
                    self.printText(f"\n\nНедоступная опция: '{command}'.\n\n")
            else:
                valid_options = [option for option in self.current_node.options if self.checkOptionRequirements(option)]
                if 0 <= option_index < len(valid_options):
                    option = valid_options[option_index]
                    self.printText("\n\n" + option['description'] + "\n\n")
                    time.sleep(len(option['description']) * 0.015)
                    time.sleep(2)
                    self.executeOption(option)
                    self.playSoundEffect('transition')
                else:
                    self.printText(f"\n\nОпция не найдена: '{command}'.\n\n")
        else:
            self.printText(f"\n\nНеизвестная комманда: '{command}'.\n\n")

    def executeOption(self, option):
        rewards = option.get('rewards', [])
        for reward in rewards:
            if reward['type'] == 'quest':
                quest_title = reward['title']
                if not self.hasQuest(quest_title):
                    quest = Quest(quest_title, reward['description'])
                    self.quests.append(quest)
                    self.printText(f"\n- Получено: {quest.title}\n")
                    time.sleep(2)
            elif reward['type'] == 'item':
                item = Item(reward['name'], reward['description'])
                self.inventory.append(item)
                self.printText(f"\n- Получено: {item.name}\n")
                time.sleep(2)
    
        next_node_id = option['next_node']
        next_node = self.getNodeById(next_node_id)
        if next_node:
            QTimer.singleShot(len(option['description']) * 0, lambda: self.transitionToNextNode(next_node))


    def fadeDescription(self):
        animation = QPropertyAnimation(self.display, b"geometry")
        animation.setDuration(1000)
        animation.setStartValue(QRect(0, 0, self.width(), self.height()))
        animation.setEndValue(QRect(0, self.height(), self.width(), 0))
        animation.setEasingCurve(QEasingCurve.InOutQuad)
        animation.start()

    def transitionToNextNode(self, next_node):
        self.current_node = next_node
        self.updateDisplayText("\n\n" + next_node.text + "\n\n")
        self.showOptions()

    def getNodeById(self, node_id):
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None

    def playSoundEffect(self, effect):
        print(f"Playing {effect} sound effect.")

    def selectSaveSlot(self):
        dialog = SaveLoadDialog(self, 'Сохранение игры', 'save')
        if dialog.exec_() == QDialog.Accepted:
            slot = dialog.getSelectedSlot()
            if slot:
                self.saveGame(slot)

    def saveGame(self, slot):
        state = {
            'current_node': self.current_node.id if self.current_node else None,
            'inventory': [{'name': item.name, 'description': item.description} for item in self.inventory],
            'quests': [{'title': quest.title, 'description': quest.description, 'completed': quest.completed} for quest in self.quests]
        }
        try:
            with open(f'game_save_{slot}.json', 'w') as f:
                json.dump(state, f)
            self.printText(f"\n\nИгра сохранена в слот {slot}.\n\n")
        except Exception as e:
            self.printText(f"\n\nОшибка при сохранении: {str(e)}\n\n")

    def selectLoadSlot(self):
        dialog = SaveLoadDialog(self, 'Загрузка игры', 'load')
        if dialog.exec_() == QDialog.Accepted:
            slot = dialog.getSelectedSlot()
            if slot:
                self.loadGame(slot)

    def loadGame(self, slot):
        try:
            with open(f'game_save_{slot}.json', 'r') as f:
                state = json.load(f)
            self.current_node = self.getNodeById(state['current_node'])
            self.inventory = [Item(item['name'], item['description']) for item in state['inventory']]
            self.quests = [Quest(quest['title'], quest['description'], quest['completed']) for quest in state['quests']]
            self.updateDisplayText("\n\nИгра загружена.\n\n")
            self.updateDisplayText("\n\n" + self.current_node.text + "\n\n")
            self.showOptions()
        except FileNotFoundError:
            self.printText(f"\n\nСохранение в слоте {slot} не найдено.\n\n")
        except Exception as e:
            self.printText(f"\n\nОшибка при загрузке игры: {str(e)}\n\n")

    def loadGameData(self):
        with open('Shadows_of_Night_City.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.nodes = [Node(**node_data) for node_data in data['nodes']]

    def showAsciiArt(self, ascii_art_path):
        try:
            with open(ascii_art_path, 'r') as f:
                ascii_art = f.read()
            prev_font = self.display.font()
            self.display.setFont(QFont('Thintel', 10))
            self.printText(ascii_art, fade_in=False)
            self.display.setFont(prev_font)
        except FileNotFoundError:
            self.printText("\n\nASCII арт не найден.\n\n")
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F11:
            self.toggleFullScreen() 
        if event.key() == Qt.Key_Alt:
            self.current_typing_speed = self.fast_typing_speed            
        super().keyPressEvent(event)
           

if __name__ == '__main__':
    app = QApplication(sys.argv)
    game = RetroGameInterface()
    game.show()
    game.showMainMenu()
    sys.exit(app.exec_())
