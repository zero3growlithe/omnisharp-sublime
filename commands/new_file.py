import os
import sublime
import sublime_plugin
import glob

from ..lib import helpers
from ..lib import omnisharp

class OmniSharpNewFile(sublime_plugin.TextCommand):
    
    PACKAGE_NAME = 'OmniSharp'
    TMLP_DIR = 'templates'

    def run(self, edit, tmpltype='class', paths=[]):
        print(paths)
        if (len(paths) == 0):
            if sublime.active_window().active_view().file_name() is not None:
                paths = [sublime.active_window().active_view().file_name()]
            else:
                paths = [sublime.active_window().folders()[0]]

        incomingpath = paths[0]
        if not os.path.isdir(incomingpath):
            incomingpath = os.path.dirname(incomingpath)

        self.incomingpath = incomingpath
        self.tmpltype = tmpltype
        self.view.window().show_input_panel("New File:", incomingpath + os.path.sep + "new" + tmpltype + ".cs", self._on_done, None, None)

    def _on_done(self,filename):
        originalfilename = filename

        namespace = self.get_namespace()

        filename =  os.path.basename(filename)
        filename = os.path.splitext(filename)[0]

        tmpl = self.get_code(self.tmpltype, namespace, filename)

        if len(tmpl) > 0:
            with open(originalfilename, 'w') as f:
                f.write(tmpl)

            #set params for filename
            params = {}
            params['filename'] = originalfilename
            omnisharp.get_response(self.view, '/addtoproject', self._handle_addtoproject, params)
                
            sublime.active_window().open_file(originalfilename)

    def _handle_addtoproject(self, data):
        print('file added to project')
        print(data)

    def solution_folder(self, start_path):
        last_root    = start_path
        current_root = start_path
        found_path   = None
        while found_path is None and current_root:
            pruned = False
            for root, dirs, files in os.walk(current_root):
                if not pruned:
                   try:
                      # Remove the part of the tree we already searched
                      del dirs[dirs.index(os.path.basename(last_root))]
                      pruned = True
                   except ValueError:
                      pass
                results = glob.glob(current_root + "/*.sln")
                if(len(results) > 0):
                   # if searching_for in files:
                   # found the file, stop
                   # found_path = os.path.join(root, searching_for)
                   # break
                   return os.path.basename(root)
            # Otherwise, pop up a level, search again
            last_root    = current_root
            current_root = os.path.dirname(last_root)


    def get_code(self, type, namespace, filename):
        code = ''
        file_name = "%s.tmpl" % type
        isIOError = False

        tmpl_dir = 'Packages/' + self.PACKAGE_NAME + '/' + self.TMLP_DIR + '/'
        user_tmpl_dir = 'Packages/User/' + \
            self.PACKAGE_NAME + '/' + self.TMLP_DIR + '/'


        self.user_tmpl_path = os.path.join(user_tmpl_dir, file_name)
        self.tmpl_path = os.path.join(tmpl_dir, file_name)

        try:
            code = sublime.load_resource(self.user_tmpl_path)
        except IOError:
            try:
                code = sublime.load_resource(self.tmpl_path)
            except IOError:
                isIOError = True

        if isIOError:
            sublime.message_dialog('[Warning] No such file: ' + self.tmpl_path
                                   + ' or ' + self.user_tmpl_path)

        code = code.replace('${namespace}', namespace)
        code = code.replace('${classname}', filename)

        return code


    def get_namespace(self):
        # Try to create namespace based on path relative to project.json file
        current_dir = self.incomingpath
        while current_dir:
            check_file = os.path.join(current_dir, 'project.json')
            print('get_namespace: looking for {0}'.format(check_file))
            if os.path.isfile(check_file):
                indexpos = len(os.path.dirname(current_dir)) + 1
                namespace = self.incomingpath[indexpos:].replace(os.path.sep, '.')
                print('get_namespace: {0} {1} {2}'.format(current_dir, indexpos, namespace))
                return namespace
            else:
                current_dir = os.path.dirname(current_dir)

        # Fallback to the old way of doing it
        root = sublime.active_window().folders()[0]
        root = os.path.basename(root)
        indexpos = self.incomingpath.index(root)
        return incomingpath[indexpos:].replace(os.path.sep, '.')
