import json
import re

REGEX_TYPE_ARRAY = re.compile(r" (\[\d+\])")

def load_json(filename: str) -> dict:
	with open(filename, "r") as file:
		data = json.load(file)

	return data

def fix_type_array_format(type, name):
	array = REGEX_TYPE_ARRAY.search(type)

	if array == None:
		return type, name

	return type.split(" ")[0], name + array.group(1)

def fix_colons(name):
	return name.replace("::", "__")

def fix_function_type_format(type, name):
	if "(*)" in type:
		return type.replace("(*)", f"(* {name})"), ""

	return type, name

def fix_pointer_reference(type):
	return type.replace("&", "*")

def write_start(file):
	file.write("#include <stdint.h>\n")
	file.write("#include <stddef.h>\n")
	file.write("#include <stdbool.h>\n")
	file.write("\n")
	file.write("#ifndef STEAM_API_H\n")
	file.write("#define STEAM_API_H\n")
	file.write("\n")

def write_end(file):
	file.write("#endif")

def write_struct_declarations(file, structs):
	for struct in structs:
		print(f" * {struct['struct']}")

		file.write(f"typedef struct {struct['struct']} {struct['struct']};\n")

	file.write("typedef struct SteamDatagramRelayAuthTicket SteamDatagramRelayAuthTicket;\n")
	file.write("typedef struct ScePadTriggerEffectParam ScePadTriggerEffectParam;\n")

	file.write("\n")

def write_enumeration_declarations(file, enumerations):
	for enumeration in enumerations:
		name = enumeration['enumname']

		print(f" * {name}")

		file.write(f"enum {name} : int;\n")
		file.write(f"typedef enum {name} {name};\n")
		file.write("\n")

def write_interface_declarations(file, interfaces):
	for interface in interfaces:
		print(f" * {interface['classname']}")

		file.write(f"typedef struct {interface['classname']} {interface['classname']};\n")

	file.write("\n")

def write_type_definitions(file, type_definitions):
	for type in type_definitions:
		print(f" * {type['typedef']}")

		type_type, type_name = type["type"], type["typedef"]
		type_type, type_name = fix_type_array_format(type_type, type_name)
		type_type, type_name = fix_function_type_format(type_type, type_name)

		file.write(f"typedef {type_type} {type_name};\n")

	file.write("typedef uint64 CSteamID;\n")
	file.write("typedef uint64 CGameID;\n")
	file.write("typedef void (*SteamAPIWarningMessageHook_t)(int, const char * );")
	file.write("\n")

def write_constants(file, constants):
	for constant in constants:
		print(f" * {constant['constname']}")

		constant_type, constant_name = constant["consttype"], constant["constname"]
		constant_type, constant_name = fix_type_array_format(constant_type, constant_name)

		file.write(f"const {constant_type} {constant_name} = {constant['constval']};\n")

	file.write("\n")

def write_enumerations(file, enumerations):
	for enumeration in enumerations:
		print(f" * {enumeration['enumname']}")

		file.write(f"enum {enumeration['enumname']} : int {{\n")

		for value in enumeration["values"]:
			file.write(f"\t{value['name']} = {value['value']},\n")

		file.write("};\n")
		file.write("\n")

def write_structs(file, structs):
	for struct in structs:
		# the json doesnt tell us how to generate this in a good way
		# so it generates with "SteamInputActionEvent_t::AnalogAction_t"
		# which is not usable in c because its cpp
		if struct['struct'] == "SteamInputActionEvent_t":
			print(f" ! SKIPPING {struct['struct']}")
			continue

		print(f" * {struct['struct']}")

		file.write(f"struct {struct['struct']} {{\n")

		for field in struct["fields"]:
			field_type, field_name = fix_colons(field["fieldtype"]), field["fieldname"]
			field_type, field_name = fix_type_array_format(field_type, field_name)
			field_type, field_name = fix_function_type_format(field_type, field_name)

			file.write(f"\t{field_type} {field_name};\n")

		file.write("};\n")

		if "methods" not in struct:
			file.write("\n")
			continue

		for method in struct["methods"]:
			file.write(f"{method['returntype']} {method['methodname_flat']}({struct['struct']} {struct['struct'][0].lower() + struct['struct'][1:]});\n")

		file.write("\n")

def write_callback_structs(file, callback_structs):
	for callback in callback_structs:
		print(f" * {callback['struct']} ({callback['callback_id']})")

		file.write(f"const int {callback['struct']}_CALLBACK_ID = {callback['callback_id']};\n")
		file.write(f"struct {callback['struct']} {{\n")

		for field in callback["fields"]:
			field_type, field_name = field["fieldtype"], field["fieldname"]
			field_type, field_name = fix_type_array_format(field_type, field_name)

			file.write(f"\t{field_type} {field_name};\n")

		file.write("};\n")

		if "enums" in callback:
			for enumeration in callback["enums"]:
				file.write("typedef enum {\n")
				for value in enumeration["values"]:
					file.write(f"\t{value['name']} = {value['value']},\n")
				file.write(f"}} {fix_colons(enumeration['fqname'])};\n")

		file.write("\n")

def write_interfaces(file, interfaces):
	for interface in interfaces:
		print(f" * {interface['classname']}")

		if "enums" in interface:
			for enumeration in interface["enums"]:
				file.write("typedef enum {\n")
				for value in enumeration["values"]:
					file.write(f"\t{value['name']} = {value['value']},\n")
				file.write(f"}} {fix_colons(enumeration['fqname'])};\n")

		for method in interface["methods"]:
			if method['methodname_flat'] in ["SteamAPI_ISteamNetworkingSockets_ConnectP2PCustomSignaling", "SteamAPI_ISteamNetworkingSockets_ReceivedP2PCustomSignal"]:
				print(f"   ! SKIPPING {method['methodname']}")
				continue

			print(f"   o {method['methodname']}")

			file.write(f"{method['returntype']} {method['methodname_flat']}(")

			parameter_count = len(method["params"])
			for index, parameter in enumerate(method["params"]):
				file.write(f"{fix_pointer_reference(fix_colons(parameter['paramtype']))} {parameter['paramname']}")

				if index + 1 != parameter_count:
					file.write(", ")

			file.write(");\n")

		file.write("\n")

def main():
	steam_api = load_json("steam_api.json")

	with open("steam_api.h", "w") as file:
		write_start(file)

		print("Generating (callback) struct declarations")
		write_struct_declarations(file, steam_api["callback_structs"]+steam_api["structs"])

		print("Generating enumeration declarations")
		write_enumeration_declarations(file, steam_api["enums"])

		print("Generating interface declarations")
		write_interface_declarations(file, steam_api["interfaces"])

		print("Generating type definitions!")
		write_type_definitions(file, steam_api["typedefs"])

		print("Generating constants!")
		write_constants(file, steam_api["consts"])

		print("Generating enumerations!")
		write_enumerations(file, steam_api["enums"])

		print("Generating structs!")
		write_structs(file, steam_api["structs"])

		print("Generating callback structs!")
		write_callback_structs(file, steam_api["callback_structs"])

		print("Generating interfaces!")
		write_interfaces(file, steam_api["interfaces"])

		write_end(file)

if __name__ == "__main__":
	main()
