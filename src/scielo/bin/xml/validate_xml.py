import reuse.xml.xml_java as xml_java

from reuse.input_output.parameters import Parameters 

import sys
import os, shutil

sys.argv = [ arg.replace('\\', '/') for arg in sys.argv  ]
xml_filename = ''

required_parameters = ['', 'xml filename', 'ctrl filename', 'err filename', 'validate' ]
parameters = Parameters(required_parameters)
if parameters.check_parameters(sys.argv):
    script, xml_filename, ctrl_filename,  err_filename, DTD_path = sys.argv
else:
    required_parameters = ['', 'xml filename', 'ctrl filename', 'err filename']
    parameters = Parameters(required_parameters)
    if parameters.check_parameters(sys.argv):
        script, xml_filename, ctrl_filename,  err_filename = sys.argv
   
if len(xml_filename)>0:
    result_filename = err_filename + '.tmp'

    if os.path.exists(ctrl_filename):
        os.unlink(ctrl_filename)

    if '/' in script:
        current_path = os.path.dirname(script).replace('\\', '/')
    else:
        current_path = os.getcwd()
    
    xml_java.jar_transform = current_path + '/../jar/saxonb9-1-0-8j/saxon9.jar' 
    xml_java.jar_validate = current_path + '/../jar/XMLCheck.jar'
    xml_java.validate(xml_filename, DTD_path, result_filename, err_filename)

    if os.path.exists(result_filename):
        shutil.copyfile(result_filename, ctrl_filename)
        f = open(result_filename)
        print(f.read())
        f.close()
        shutil.copyfile(result_filename, ctrl_filename)
        os.unlink(result_filename)
    if os.path.exists(err_filename):
        shutil.copyfile(err_filename, ctrl_filename)