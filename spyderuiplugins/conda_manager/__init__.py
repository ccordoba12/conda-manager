# -*- coding:utf-8 -*-
#
# Copyright © 2015 Gonzalo Peña-Castellanos (@goanpeca)
#
# Licensed under the terms of the MIT License

"""
Conda Package Manager Plugin.
"""

import gettext
import os.path as osp

from qtpy.QtCore import Qt, Signal
from qtpy.QtWidgets import QGridLayout, QGroupBox, QVBoxLayout

from spyderlib.plugins import SpyderPluginMixin, PluginConfigPage

from conda_manager.widgets import CondaPackagesWidget
from conda_manager.utils import get_icon

_ = gettext.gettext


class CondaPackagesConfigPage(PluginConfigPage):
    """ """
    def setup_page(self):
        network_group = QGroupBox(_("Network settings"))
        self.checkbox_proxy = self.create_checkbox(_("Use network proxy"),
                                                   'use_proxy_flag',
                                                   default=False)
        server = self.create_lineedit(_('Server'), 'server', default='',
                                      alignment=Qt.Horizontal)
        port = self.create_lineedit(_('Port'), 'port', default='',
                                    alignment=Qt.Horizontal)
        user = self.create_lineedit(_('User'), 'user', default='',
                                    alignment=Qt.Horizontal)
        password = self.create_lineedit(_('Password'), 'password', default='',
                                        alignment=Qt.Horizontal)

        self.widgets = [server, port, user, password]

        network_layout = QGridLayout()
        network_layout.addWidget(self.checkbox_proxy, 0, 0)
        network_layout.addWidget(server.label, 1, 0)
        network_layout.addWidget(server.textbox, 1, 1)
        network_layout.addWidget(port.label, 1, 2)
        network_layout.addWidget(port.textbox, 1, 3)
        network_layout.addWidget(user.label, 2, 0)
        network_layout.addWidget(user.textbox, 2, 1)
        network_layout.addWidget(password.label, 2, 2)
        network_layout.addWidget(password.textbox, 2, 3)
        network_group.setLayout(network_layout)

        vlayout = QVBoxLayout()
        vlayout.addWidget(network_group)
        vlayout.addStretch(1)
        self.setLayout(vlayout)

        # Signals
        self.checkbox_proxy.clicked.connect(self.proxy_settings)
        self.proxy_settings()

    def proxy_settings(self):
        """ """
        state = self.checkbox_proxy.checkState()
        disabled = True

        if state == 2:
            disabled = False
        elif state == 0:
            disabled = True

        for widget in self.widgets:
            widget.setDisabled(disabled)


class CondaPackages(CondaPackagesWidget, SpyderPluginMixin):
    """Conda package manager based on conda and conda-api."""
    CONF_SECTION = 'conda_manager'
    CONFIGWIDGET_CLASS = CondaPackagesConfigPage

    sig_environment_created = Signal()

    def __init__(self, parent=None):
        CondaPackagesWidget.__init__(self, parent=parent)
        SpyderPluginMixin.__init__(self, parent)

	self.root_env = 'root'
        self._env_to_set = self.get_active_env()


        # Initialize plugin
        self.initialize_plugin()

    # ------ SpyderPluginWidget API -------------------------------------------
    def get_plugin_title(self):
        """Return widget title"""
        return _("Conda package manager")

    def get_plugin_icon(self):
        """Return widget icon"""
        return get_icon('condapackages.png')

    def get_focus_widget(self):
        """
        Return the widget to give focus to when
        this plugin's dockwidget is raised on top-level
        """
        return self.textbox_search

    def get_plugin_actions(self):
        """Return a list of actions related to plugin"""
        return []

    def on_first_registration(self):
        """Action to be performed on first plugin registration"""
        self.main.tabify_plugins(self.main.inspector, self)
        self.dockwidget.hide()

    def register_plugin(self):
        """Register plugin in Spyder's main window"""
        main = self.main
        main.add_dockwidget(self)

        if getattr(main.projectexplorer, 'sig_project_closed', False):
            pe = main.projectexplorer
            pe.condamanager = self
            pe.sig_project_closed.connect(self.project_closed)
            pe.sig_project_loaded.connect(self.project_loaded)
            self.sig_worker_ready.connect(self._after_load)
            self.sig_environment_created.connect(pe.sig_environment_created)

    def refresh_plugin(self):
        """Refresh pylint widget"""
        pass

    def closing_plugin(self, cancelable=False):
        """Perform actions before parent main window is closed"""
        return True

    def apply_plugin_settings(self, options):
        """Apply configuration file's plugin settings"""
        pass

    # ------ Public API -------------------------------------------------------
    def create_env(self, name, package):
        self.create_environment(name, package)
        if self.dockwidget.isHidden():
            self.dockwidget.show()
        self.dockwidget.raise_()

    def set_env(self, env):
        """ """
#        self.sig_packages_ready.disconnect()
        self.set_environment(env)
        # TODO:

    # ------ Project explorer API ---------------------------------------------
    def get_active_project_path(self):
        """ """
        pe = self.main.projectexplorer
        if pe:
            project = pe.get_active_project()
            if project:
                return project.get_root()

    def project_closed(self, project_path):
        """ """
        self.set_env(self.root_env)

    def project_loaded(self, project_path):
        """ """
        name = osp.basename(project_path)
        env = self.get_prefix_envname(name)

        #self.sig_packages_ready.connect(self.set_env)

        #print('name, envprefix', name, env_prefix)
        # If None, no matching package was found!

        if env:
            self._env_to_set = env
            self.set_env(env)

    def _after_load(self):
        """ """
        active_env = self.get_active_env()
        if active_env == 'root':  # Root
            self.disable_widgets()
        else:
            self.enable_widgets()


# =============================================================================
# The following statements are required to register this 3rd party plugin:
# =============================================================================
# Only register plugin if conda is found on the system
PLUGIN_CLASS = CondaPackages
