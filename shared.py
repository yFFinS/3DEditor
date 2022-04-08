class EditorShared:
    __editor = None

    @staticmethod
    def init(editor):
        EditorShared.__editor = editor

    @staticmethod
    def get_editor():
        return EditorShared.__editor

    @staticmethod
    def get_scene():
        return EditorShared.get_editor().get_scene()

    @staticmethod
    def get_gl_widget():
        return EditorShared.get_editor().get_gl_widget()

    @staticmethod
    def get_scene_explorer():
        return EditorShared.get_editor().get_scene_explorer()
