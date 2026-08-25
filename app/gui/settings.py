"""Settings and Configuration Page for JARVIS Desktop Agent."""

from pathlib import Path
from typing import Any, Callable, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.config import Config


class SettingsPage(QWidget):
    """Configuration management view with credential masking and live updates."""

    config_saved = Signal(Config)

    def __init__(self, config: Config, parent=None) -> None:
        super().__init__(parent)
        self.config = config

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Header
        title = QLabel("System Settings & Providers")
        title.setStyleSheet("color: #F8FAFC; font-size: 20px; font-weight: bold;")
        subtitle = QLabel("Configure remote AI brains, voice models, vision thresholds, and security policies")
        subtitle.setStyleSheet("color: #94A3B8; font-size: 12px; margin-bottom: 12px;")
        main_layout.addWidget(title)
        main_layout.addWidget(subtitle)

        # Scroll Area for forms
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { background-color: transparent; border: none; }")

        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setSpacing(16)

        # 1. AI Brain / LLM Provider Group
        llm_group = QGroupBox("AI PROVIDER CONFIGURATION")
        llm_group.setStyleSheet("QGroupBox { color: #38BDF8; font-weight: bold; border: 1px solid #334155; border-radius: 8px; margin-top: 10px; padding-top: 14px; }")
        llm_grid = QGridLayout(llm_group)
        llm_grid.setSpacing(10)

        llm_grid.addWidget(QLabel("LLM Provider:"), 0, 0)
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["openai_compatible", "anthropic", "ollama", "mock"])
        self.provider_combo.setCurrentText(self.config.llm.provider)
        llm_grid.addWidget(self.provider_combo, 0, 1)

        llm_grid.addWidget(QLabel("Base URL:"), 1, 0)
        self.base_url_input = QLineEdit(self.config.llm.base_url)
        self.base_url_input.setPlaceholderText("https://api.openai.com/v1 or custom provider endpoint")
        llm_grid.addWidget(self.base_url_input, 1, 1)

        llm_grid.addWidget(QLabel("API Key:"), 2, 0)
        key_layout = QHBoxLayout()
        self.api_key_input = QLineEdit(self.config.llm.api_key)
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setPlaceholderText("Enter API Key (will be masked and protected)")
        key_layout.addWidget(self.api_key_input, 1)

        self.toggle_key_btn = QPushButton("👁️")
        self.toggle_key_btn.setFixedWidth(36)
        self.toggle_key_btn.clicked.connect(self._toggle_api_key_visibility)
        key_layout.addWidget(self.toggle_key_btn)
        llm_grid.addLayout(key_layout, 2, 1)

        llm_grid.addWidget(QLabel("Model ID:"), 3, 0)
        self.model_input = QLineEdit(self.config.llm.model)
        self.model_input.setPlaceholderText("e.g. gpt-4o, claude-3-5-sonnet-20241022, qwen3:4b")
        llm_grid.addWidget(self.model_input, 3, 1)

        llm_grid.addWidget(QLabel("Temperature:"), 4, 0)
        self.temp_spin = QDoubleSpinBox()
        self.temp_spin.setRange(0.0, 1.0)
        self.temp_spin.setSingleStep(0.05)
        self.temp_spin.setValue(self.config.llm.temperature)
        llm_grid.addWidget(self.temp_spin, 4, 1)

        form_layout.addWidget(llm_group)

        # 2. Voice & Speech Group
        voice_group = QGroupBox("VOICE & SPEECH SYNTHESIS")
        voice_group.setStyleSheet("QGroupBox { color: #38BDF8; font-weight: bold; border: 1px solid #334155; border-radius: 8px; margin-top: 10px; padding-top: 14px; }")
        v_grid = QGridLayout(voice_group)
        v_grid.setSpacing(10)

        self.voice_enabled_chk = QCheckBox("Enable Voice Input & Speech Output")
        self.voice_enabled_chk.setChecked(self.config.voice.enabled)
        v_grid.addWidget(self.voice_enabled_chk, 0, 0, 1, 2)

        self.wakeword_chk = QCheckBox("Enable Wake-Word Detection ('Hey JARVIS')")
        self.wakeword_chk.setChecked(self.config.voice.wake_word_enabled)
        v_grid.addWidget(self.wakeword_chk, 1, 0, 1, 2)

        v_grid.addWidget(QLabel("TTS Provider:"), 2, 0)
        self.tts_combo = QComboBox()
        self.tts_combo.addItems(["pyttsx3", "piper", "mock"])
        self.tts_combo.setCurrentText(self.config.voice.tts_provider)
        v_grid.addWidget(self.tts_combo, 2, 1)

        form_layout.addWidget(voice_group)

        # 3. Vision & Study Monitor
        vision_group = QGroupBox("COMPUTER VISION & STUDY ASSISTANT")
        vision_group.setStyleSheet("QGroupBox { color: #38BDF8; font-weight: bold; border: 1px solid #334155; border-radius: 8px; margin-top: 10px; padding-top: 14px; }")
        vis_layout = QVBoxLayout(vision_group)
        vis_layout.setSpacing(8)

        self.cam_enabled_chk = QCheckBox("Enable Camera System (Disabled by default)")
        self.cam_enabled_chk.setChecked(self.config.vision.enabled)
        vis_layout.addWidget(self.cam_enabled_chk)

        self.study_eye_chk = QCheckBox("Enable Study Assistant Prolonged Eye-Closure Alerts")
        self.study_eye_chk.setChecked(self.config.vision.study_eye_detection)
        vis_layout.addWidget(self.study_eye_chk)

        self.study_away_chk = QCheckBox("Enable Study Distraction / Looking Away Alerts")
        self.study_away_chk.setChecked(self.config.vision.study_attention_detection)
        vis_layout.addWidget(self.study_away_chk)

        form_layout.addWidget(vision_group)

        # 4. Security & Permissions
        sec_group = QGroupBox("SECURITY & PERMISSION ENGINE")
        sec_group.setStyleSheet("QGroupBox { color: #38BDF8; font-weight: bold; border: 1px solid #334155; border-radius: 8px; margin-top: 10px; padding-top: 14px; }")
        sec_layout = QVBoxLayout(sec_group)
        sec_layout.setSpacing(8)

        self.sec_high_chk = QCheckBox("Require Confirmation for High-Risk Actions (File Deletion, etc.)")
        self.sec_high_chk.setChecked(self.config.security.require_confirmation_high_risk)
        sec_layout.addWidget(self.sec_high_chk)

        self.sec_med_chk = QCheckBox("Require Confirmation for Medium-Risk Actions")
        self.sec_med_chk.setChecked(self.config.security.require_confirmation_medium_risk)
        sec_layout.addWidget(self.sec_med_chk)

        form_layout.addWidget(sec_group)

        scroll.setWidget(form_widget)
        main_layout.addWidget(scroll, 1)

        # Save Button Row
        btn_box = QHBoxLayout()
        btn_box.addStretch()

        self.save_btn = QPushButton("Save Settings & Apply")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: white;
                font-weight: bold;
                font-size: 14px;
                padding: 10px 24px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover { background-color: #059669; }
        """)
        self.save_btn.clicked.connect(self._save_settings)
        btn_box.addWidget(self.save_btn)
        main_layout.addLayout(btn_box)

    def _toggle_api_key_visibility(self) -> None:
        if self.api_key_input.echoMode() == QLineEdit.Password:
            self.api_key_input.setEchoMode(QLineEdit.Normal)
        else:
            self.api_key_input.setEchoMode(QLineEdit.Password)

    def _save_settings(self) -> None:
        self.config.llm.provider = self.provider_combo.currentText()
        self.config.llm.base_url = self.base_url_input.text().strip()
        self.config.llm.api_key = self.api_key_input.text().strip()
        self.config.llm.model = self.model_input.text().strip()
        self.config.llm.temperature = self.temp_spin.value()

        self.config.voice.enabled = self.voice_enabled_chk.isChecked()
        self.config.voice.wake_word_enabled = self.wakeword_chk.isChecked()
        self.config.voice.tts_provider = self.tts_combo.currentText()

        self.config.vision.enabled = self.cam_enabled_chk.isChecked()
        self.config.vision.study_eye_detection = self.study_eye_chk.isChecked()
        self.config.vision.study_attention_detection = self.study_away_chk.isChecked()

        self.config.security.require_confirmation_high_risk = self.sec_high_chk.isChecked()
        self.config.security.require_confirmation_medium_risk = self.sec_med_chk.isChecked()

        # Save to .env
        self.config.save_to_env()
        self.config_saved.emit(self.config)
        QMessageBox.information(self, "Settings Saved", "Configuration has been saved successfully.")
