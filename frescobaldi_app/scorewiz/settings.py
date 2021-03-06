# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2012 by Wilbert Berendsen
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# See http://www.gnu.org/licenses/ for more information.

"""
The score settings widget.
"""

from __future__ import unicode_literals

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import app
import po.setup
import language_names
import listmodel
import lilypondinfo

from . import scoreproperties

class SettingsWidget(QWidget):
    def __init__(self, parent):
        super(SettingsWidget, self).__init__(parent)
        grid = QGridLayout()
        self.setLayout(grid)
        
        self.scoreProperties = ScoreProperties(self)
        self.generalPreferences = GeneralPreferences(self)
        self.lilyPondPreferences = LilyPondPreferences(self)
        self.instrumentNames = InstrumentNames(self)
        
        grid.addWidget(self.scoreProperties, 0, 0)
        grid.addWidget(self.generalPreferences, 0, 1)
        grid.addWidget(self.lilyPondPreferences, 1, 0)
        grid.addWidget(self.instrumentNames, 1, 1)
    
    def clear(self):
        self.scoreProperties.tempo.clear()
        self.scoreProperties.keyNote.setCurrentIndex(0)
        self.scoreProperties.keyMode.setCurrentIndex(0)
        self.scoreProperties.pickup.setCurrentIndex(0)


class ScoreProperties(QGroupBox, scoreproperties.ScoreProperties):
    def __init__(self, parent):
        super(ScoreProperties, self).__init__(parent)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        self.createWidgets()
        self.layoutWidgets(layout)
        
        app.translateUI(self)
        
        scorewiz = self.window()
        scorewiz.pitchLanguageChanged.connect(self.setPitchLanguage)
        self.setPitchLanguage(scorewiz.pitchLanguage())
        scorewiz.accepted.connect(self.saveCompletions)
        
    def translateUI(self):
        self.translateWidgets()
        self.setTitle(_("Score properties"))
    


class GeneralPreferences(QGroupBox):
    def __init__(self, parent):
        super(GeneralPreferences, self).__init__(parent)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        self.typq = QCheckBox()
        self.tagl = QCheckBox()
        self.barnum = QCheckBox()
        self.midi = QCheckBox()
        self.metro = QCheckBox()
        self.paperSizeLabel = QLabel()
        self.paper = QComboBox()
        self.paper.addItems(paperSizes)
        self.paperLandscape = QCheckBox(enabled=False)
        self.paper.activated.connect(self.slotPaperChanged)
        
        layout.addWidget(self.typq)
        layout.addWidget(self.tagl)
        layout.addWidget(self.barnum)
        layout.addWidget(self.midi)
        layout.addWidget(self.metro)
        
        box = QHBoxLayout(spacing=2)
        box.addWidget(self.paperSizeLabel)
        box.addWidget(self.paper)
        box.addWidget(self.paperLandscape)
        layout.addLayout(box)
        app.translateUI(self)
        
        self.loadSettings()
        self.window().finished.connect(self.saveSettings)
        
    def translateUI(self):
        self.setTitle(_("General preferences"))
        self.typq.setText(_("Use typographical quotes"))
        self.typq.setToolTip(_(
            "Replace normal quotes in titles with nice typographical quotes."))
        self.tagl.setText(_("Remove default tagline"))
        self.tagl.setToolTip(_(
            "Suppress the default tagline output by LilyPond."))
        self.barnum.setText(_("Remove bar numbers"))
        self.barnum.setToolTip(_(
            "Suppress the display of measure numbers at the beginning of "
            "every system."))
        self.midi.setText(_("Create MIDI output"))
        self.midi.setToolTip(_(
            "Create a MIDI file in addition to the PDF file."))
        self.metro.setText(_("Show metronome mark"))
        self.metro.setToolTip(_(
            "If checked, show the metronome mark at the beginning of the "
            "score. The MIDI output also uses the metronome setting."))
        # paper size:
        self.paperSizeLabel.setText(_("Paper size:"))
        self.paper.setItemText(0, _("Default"))
        self.paperLandscape.setText(_("Landscape"))
  
    def slotPaperChanged(self, index):
        self.paperLandscape.setEnabled(bool(index))
    
    def getPaperSize(self):
        """Returns the configured papersize or the empty string for default."""
        return paperSizes[self.paper.currentIndex()]
    
    def loadSettings(self):
        s = QSettings()
        s.beginGroup('scorewiz/preferences')
        self.typq.setChecked(s.value('typographical_quotes', True) not in (False, 'false'))
        self.tagl.setChecked(s.value('remove_tagline', False) in (True, 'true'))
        self.barnum.setChecked(s.value('remove_barnumbers', False) in (True, 'true'))
        self.midi.setChecked(s.value('midi', True) not in (False, 'false'))
        self.metro.setChecked(s.value('metronome_mark', False) in (True, 'true'))
        psize = s.value('paper_size', '')
        enable = bool(psize and psize in paperSizes)
        self.paper.setCurrentIndex(paperSizes.index(psize) if enable else 0)
        self.paperLandscape.setChecked(s.value('paper_landscape', False) in (True, 'true'))
        self.paperLandscape.setEnabled(enable)

    def saveSettings(self):
        s = QSettings()
        s.beginGroup('scorewiz/preferences')
        s.setValue('typographical_quotes', self.typq.isChecked())
        s.setValue('remove_tagline', self.tagl.isChecked())
        s.setValue('remove_barnumbers', self.barnum.isChecked())
        s.setValue('midi', self.midi.isChecked())
        s.setValue('metronome_mark', self.metro.isChecked())
        s.setValue('paper_size', paperSizes[self.paper.currentIndex()])
        s.setValue('paper_landscape', self.paperLandscape.isChecked())

        
class InstrumentNames(QGroupBox):
    def __init__(self, parent):
        super(InstrumentNames, self).__init__(parent, checkable=True, checked=True)
        
        grid = QGridLayout()
        self.setLayout(grid)
        
        self.firstSystemLabel = QLabel()
        self.firstSystem = QComboBox()
        self.firstSystemLabel.setBuddy(self.firstSystem)
        self.otherSystemsLabel = QLabel()
        self.otherSystems = QComboBox()
        self.otherSystemsLabel.setBuddy(self.otherSystems)
        self.languageLabel = QLabel()
        self.language = QComboBox()
        self.languageLabel.setBuddy(self.language)

        self.firstSystem.setModel(listmodel.ListModel(
            (lambda: _("Long"), lambda: _("Short")), self.firstSystem,
            display = listmodel.translate))
        self.otherSystems.setModel(listmodel.ListModel(
            (lambda: _("Long"), lambda: _("Short"), lambda: _("None")), self.otherSystems,
            display = listmodel.translate))
        
        self._langs = l = ['','C']
        l.extend(sorted(po.available()))
        def display(lang):
            if lang == 'C':
                return _("English (untranslated)")
            elif not lang:
                return _("Default")
            return language_names.languageName(lang, po.setup.current())
        self.language.setModel(listmodel.ListModel(l, self.language, display=display))
        
        grid.addWidget(self.firstSystemLabel, 0, 0)
        grid.addWidget(self.firstSystem, 0, 1)
        grid.addWidget(self.otherSystemsLabel, 1, 0)
        grid.addWidget(self.otherSystems, 1, 1)
        grid.addWidget(self.languageLabel, 2, 0)
        grid.addWidget(self.language, 2, 1)
        app.translateUI(self)
        self.loadSettings()
        self.window().finished.connect(self.saveSettings)
        
    def translateUI(self):
        self.setTitle(_("Instrument names"))
        self.firstSystemLabel.setText(_("First system:"))
        self.otherSystemsLabel.setText(_("Other systems:"))
        self.languageLabel.setText(_("Language:"))
        self.firstSystem.setToolTip(_(
            "Use long or short instrument names before the first system."))
        self.otherSystems.setToolTip(_(
            "Use short, long or no instrument names before the next systems."))
        self.language.setToolTip(_(
            "Which language to use for the instrument names."))
        self.firstSystem.model().update()
        self.otherSystems.model().update()
        self.language.model().update()
    
    def getLanguage(self):
        """Returns the language the user has set.
        
        '' means:  default (use same translation as system)
        'C' means: English (untranslated)
        or a languagecode that is available in Frescobaldi's translation.
        
        """
        return self._langs[self.language.currentIndex()]

    def loadSettings(self):
        s = QSettings()
        s.beginGroup('scorewiz/instrumentnames')
        self.setChecked(s.value('enabled', True) not in (False, 'false'))
        allow = ['long', 'short']
        first = s.value('first', '')
        self.firstSystem.setCurrentIndex(allow.index(first) if first in allow else 0)
        allow = ['long', 'short', 'none']
        other = s.value('other', '')
        self.otherSystems.setCurrentIndex(allow.index(other) if other in allow else 2)
        language = s.value('language', '')
        self.language.setCurrentIndex(self._langs.index(language) if language in self._langs else 0)
    
    def saveSettings(self):
        s = QSettings()
        s.beginGroup('scorewiz/instrumentnames')
        s.setValue('enable', self.isChecked())
        s.setValue('first', ('long', 'short')[self.firstSystem.currentIndex()])
        s.setValue('other', ('long', 'short', 'none')[self.otherSystems.currentIndex()])
        s.setValue('language', self._langs[self.language.currentIndex()])

        
class LilyPondPreferences(QGroupBox):
    def __init__(self, parent):
        super(LilyPondPreferences, self).__init__(parent)
        
        grid = QGridLayout()
        self.setLayout(grid)
        
        self.pitchLanguageLabel = QLabel()
        self.pitchLanguage = QComboBox()
        self.versionLabel = QLabel()
        self.version = QComboBox(editable=True)
        
        self.pitchLanguage.addItem('')
        self.pitchLanguage.addItems([lang.title() for lang in sorted(scoreproperties.keyNames)])
        self.version.addItem(lilypondinfo.preferred().versionString())
        for v in ("2.14.0", "2.12.0"):
            if v != lilypondinfo.preferred().versionString():
                self.version.addItem(v)
        
        grid.addWidget(self.pitchLanguageLabel, 0, 0)
        grid.addWidget(self.pitchLanguage, 0, 1)
        grid.addWidget(self.versionLabel, 1, 0)
        grid.addWidget(self.version, 1, 1)
        
        self.pitchLanguage.activated.connect(self.slotPitchLanguageChanged)
        app.translateUI(self)
        self.loadSettings()
        self.window().finished.connect(self.saveSettings)

    def translateUI(self):
        self.setTitle(_("LilyPond"))
        self.pitchLanguageLabel.setText(_("Pitch name language:"))
        self.pitchLanguage.setToolTip(_(
            "The LilyPond language you want to use for the pitch names."))
        self.pitchLanguage.setItemText(0, _("Default"))
        self.versionLabel.setText(_("Version:"))
        self.version.setToolTip(_(
            "The LilyPond version you will be using for this document."))

    def slotPitchLanguageChanged(self, index):
        if index == 0:
            language = ''
        else:
            language = self.pitchLanguage.currentText().lower()
        self.window().setPitchLanguage(language)
        
    def loadSettings(self):
        language = self.window().pitchLanguage()
        languages = list(sorted(scoreproperties.keyNames))
        index = languages.index(language) + 1 if language in languages else 0
        self.pitchLanguage.setCurrentIndex(index)

    def saveSettings(self):
        QSettings().setValue('scorewiz/lilypond/pitch_language', self.window().pitchLanguage())


paperSizes = ['', 'a3', 'a4', 'a5', 'a6', 'a7', 'legal', 'letter', '11x17']
