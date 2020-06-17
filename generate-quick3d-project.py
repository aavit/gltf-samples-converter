#!/usr/bin/env python
import os
from shutil import copy2
from argparse import ArgumentParser
import xml.etree.cElementTree as ET

generate-quick3d-project.py -o Q:\Code\temp -b Q:\Code\qt5-5.15-msvc2019\qtbase\bin\balsam.exe -i 2.0

def copy_template_files(output_dir):
    copy2("templates/environment.hdr", output_dir)
    copy2("templates/main.cpp", output_dir)
    copy2("templates/GltfTestViewer.qml", output_dir)
    copy2("templates/gltf2TestViewer.pro", output_dir)
    copy2("templates/viewer.qrc", output_dir)

def generate_qrc_files(output_dir):
    original_dir = os.getcwd()
    os.chdir(output_dir)

    qrcList = ["viewer.qrc"]
    # for each folder, generate a qrc file for all the files in the subtree
    for model in sorted(os.listdir(".")):
        # models will only be in folders
        if not os.path.isdir(model):
            continue

        os.chdir(model)
        qrcRoot = ET.Element("RCC")
        qrcResource = ET.SubElement(qrcRoot, "qresource", prefix="/" + model)

        componentName = ""
        for resource in sorted(os.listdir(".")):
            if not os.path.isdir(resource):
                if resource.endswith(".qrc"):
                    continue
                ET.SubElement(qrcResource, "file").text = resource
                # this is the QML file, which is the name for the qrc file as well
                componentName = resource.replace(".qml", "")
            else:
                os.chdir(resource)
                for subResource in sorted(os.listdir(".")):
                    ET.SubElement(qrcResource, "file").text = resource + "/" + subResource
                os.chdir("..")
        
        tree = ET.ElementTree(qrcRoot)
        tree.write(componentName + ".qrc", encoding="utf-8", xml_declaration=True)
        qrcList.append(model + "/" + componentName + ".qrc")
        os.chdir("..")

    # append the QRC file to the .pro file
    f = open("gltf2TestViewer.pro", "a")
    if qrcList.count > 0:
        f.write("RESOURCES += \\\n")

    for qrc in qrcList:
        f.write("    " + qrc + " \\\n")
    f.close()

    os.chdir(original_dir)

def generate_tests(directory):
    os.chdir(directory)
    models = {}
    for model in sorted(os.listdir(".")):
        if not os.path.isdir(model):
            continue
        os.chdir(model)
        model_contents = os.listdir(".")
        gltf_variant_dirs = [d for d in model_contents if d.startswith("glTF")]

        for variant_dir in gltf_variant_dirs:
            model_file = [f for f in os.listdir(variant_dir)
                          if f.endswith(".glb") or f.endswith(".gltf")][0]
            os.chdir(variant_dir)
            models[model] = os.getcwd() + os.path.sep + model_file
            os.chdir("..")
            break # only handle the first found
        os.chdir("..")
    os.chdir("..")
    return models

def generate_test_list(output_dir):
    original_dir = os.getcwd()
    os.chdir(output_dir)
    tests = {}
    for test in sorted(os.listdir(".")):
        if not os.path.isdir(test):
            continue
        os.chdir(test)
        # Get the component name
        component = [f for f in os.listdir(".")
                    if f.endswith(".qml")][0]
        tests[test] = test + "/" + component
        os.chdir("..")
    os.chdir(original_dir)
    return tests

def generate_test_model(output_dir, tests):
    original_dir = os.getcwd()
    os.chdir(output_dir)
    f = open("GltfTestsModel.qml", "w")
    f.write("import QtQuick 2.15\n")

    for test in tests:
        f.write("import \"" + test + "\"\n")

    f.write("ListModel {\n")
    for test in tests:
        f.write("\tListElement {\n")
        f.write("\t\tname: \"" + test + "\"\n")
        f.write("\t\tsource: \"" + tests[test] + "\"\n")
        f.write("\t}\n")
    f.write("}\n") #ListModel

    f.close()
    os.chdir(original_dir)


parser = ArgumentParser()
parser.add_argument("-o", "--output", dest="output",
                    help="Directory to write Output", metavar="OUTPUT")
parser.add_argument("-b", "--balsam", dest="balsam",
                    help="Location of balsam tool", metavar="BALSAM")
parser.add_argument("-i", "--input", dest="input",
                    help="Location of source directory", metavar="INPUT")                                  
args = parser.parse_args()


copy_template_files(args.output)
# Generate QML from GLTF2 files
models = generate_tests(args.input)
for model in models:
    cmd = args.balsam + " -o " + args.output + os.path.sep + model + os.path.sep + " " + models[model]
    #print(cmd) 
    os.system(cmd)

# Generate QML Viewer code
tests = generate_test_list(args.output)
generate_test_model(args.output, tests)
generate_qrc_files(args.output)

#print(tests)
