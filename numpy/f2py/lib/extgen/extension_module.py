
from base import Base

class ExtensionModule(Base):

    """
    ExtensionModule(<modulename>, *components, numpy=False, provides=..)

    Hello example:

    >>> # in general use:
    >>> #   from numpy.f2py.lib.extgen import *
    >>> # instead of the following import statement
    >>> from __init__ import * #doctest: +ELLIPSIS
    Ignoring...
    >>> f = PyCFunction('hello')
    >>> f.add('printf("Hello!\\\\n");')
    >>> f.add('printf("Bye!\\\\n");')
    >>> m = ExtensionModule('foo', f)
    >>> foo = m.build #doctest: +ELLIPSIS
    exec_command...
    >>> foo.hello()
    >>> # you should now see Hello! printed to stdout stream.

    """

    container_options = dict(\
                             Header=dict(default='<KILLLINE>'),
                             TypeDef=dict(default='<KILLLINE>'),
                             Extern=dict(default='<KILLLINE>'),
                             CCode=dict(default='<KILLLINE>'),
                             CAPICode=dict(default='<KILLLINE>'),
                             ObjDecl=dict(default='<KILLLINE>'),
                             ModuleMethod=dict(suffix=',', skip_suffix_when_empty=True,
                                               default='<KILLLINE>', use_indent=True),
                             ModuleInit=dict(default='<KILLLINE>', use_indent=True),
                             )
    
    component_container_map = dict(PyCFunction = 'CAPICode')

    template = '''\
/* -*- c -*- */
/* This Python C/API extension module "%(modulename)s" is generated
   using extgen tool. extgen is part of numpy.f2py.lib package
   developed by Pearu Peterson <pearu.peterson@gmail.com>.
*/

#ifdef __cplusplus
extern \"C\" {
#endif

%(Header)s
%(TypeDef)s
%(Extern)s
%(CCode)s
%(CAPICode)s
%(ObjDecl)s

static PyObject* extgen_module;

static PyMethodDef extgen_module_methods[] = {
  %(ModuleMethod)s
  {NULL,NULL,0,NULL}
};

PyMODINIT_FUNC init%(modulename)s(void) {
  extgen_module = Py_InitModule("%(modulename)s", extgen_module_methods);
  %(ModuleInit)s
  return;
capi_error:
  if (!PyErr_Occurred()) {
    PyErr_SetString(PyExc_RuntimeError, "failed to initialize %(modulename)s module.");
  }
  return;
}

#ifdef __cplusplus
}
#endif
'''

    def initialize(self, modulename, *components, **options):
        self.modulename = modulename
        self._provides = options.get('provides',
                                     '%s_%s' % (self.__class__.__name__, modulename))
        # all Python extension modules require Python.h
        self.add(Base.get('Python.h'), 'Header')
        if options.get('numpy'):
            self.add(Base.get('arrayobject.h'), 'Header')
            self.add(Base.get('import_array'), 'ModuleInit')
        map(self.add, components)
        return

    @property
    def build(self):
        import os
        import sys
        import subprocess
        extfile = self.generate()
        srcfile = os.path.abspath('%smodule.c' % (self.modulename))
        f = open(srcfile, 'w')
        f.write(extfile)
        f.close()
        modulename = self.modulename
        setup_py = """
def configuration(parent_package='', top_path = ''):
    from numpy.distutils.misc_util import Configuration
    config = Configuration('',parent_package,top_path)
    config.add_extension('%(modulename)s',
                         sources = ['%(srcfile)s'])
    return config
if __name__ == '__main__':
    from numpy.distutils.core import setup
    setup(configuration=configuration)
""" % (locals())
        setupfile = os.path.abspath('setup_extgen.py')
        f = open(setupfile, 'w')
        f.write(setup_py)
        f.close()
        setup_args = ['build_ext','--build-lib','.']
        setup_cmd = ' '.join([sys.executable,setupfile]+setup_args)
        build_dir = '.'
        from numpy.distutils.exec_command import exec_command
        sts = exec_command(setup_cmd)
        #p = subprocess.Popen(setup_cmd, cwd=build_dir, shell=True, stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        #sts = os.waitpid(p.pid, 0)
        if sts[0]:
            raise "Failed to build (status=%s)." % (`sts`)
        exec 'import %s as m' % (modulename)
        return m

def _test():
    import doctest
    doctest.testmod()
    
if __name__ == "__main__":
    _test()
