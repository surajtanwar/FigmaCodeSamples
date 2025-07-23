import json

SDB_TARGET_IP = "192.168.1.101"
LOOP_COUNT = 1
APP_NAME = "homescreen"
SLEEP_DURATION = 2

with open("figma_design_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

all_nodes = {}

def flatten_nodes(node):
    if isinstance(node, dict):
        if 'id' in node:
            all_nodes[node['id']] = node
        if 'children' in node:
            for child in node['children']:
                flatten_nodes(child)

flatten_nodes(data['document'])

# Patch: add parent references to all_nodes
for n in all_nodes.values():
    if 'children' in n:
        for child in n['children']:
            if isinstance(child, dict) and 'id' in child:
                all_nodes[child['id']]['parent'] = n['id']

def find_frame(n):
    parent_id = n.get('parent', None)
    while parent_id:
        parent = all_nodes.get(parent_id)
        if parent and parent.get('type') == 'FRAME':
            return parent
        if parent:
            parent_id = parent.get('parent', None)
        else:
            break
    return None

def get_relative_coords(node):
    frame = find_frame(node)
    frame_x = frame['absoluteBoundingBox']['x'] if frame and 'absoluteBoundingBox' in frame else 0
    frame_y = frame['absoluteBoundingBox']['y'] if frame and 'absoluteBoundingBox' in frame else 0
    node_x = node['absoluteBoundingBox']['x'] if 'absoluteBoundingBox' in node else None
    node_y = node['absoluteBoundingBox']['y'] if 'absoluteBoundingBox' in node else None
    rel_x = node_x - frame_x if node_x is not None and frame_x is not None else None
    rel_y = node_y - frame_y if node_y is not None and frame_y is not None else None
    return rel_x, rel_y

testcases = []
for node_id, node in all_nodes.items():
    if 'interactions' in node and isinstance(node['interactions'], list):
        for interaction in node['interactions']:
            actions = interaction.get("actions", [])
            for action in actions:
                if not action:
                    continue
                destination_id = action.get("destinationId")
                destination_name = all_nodes.get(destination_id, {}).get("name", "Unknown") if destination_id else None
                source_name = node.get('name', node_id)
                tc_name = f"{source_name} to {destination_name}"
                steps = []
                steps.append(f"APP, {APP_NAME}")
                # Use CLICK if node has a visible name, else use CLICK_COORDS
                if node.get('name') and node['name'].strip():
                    steps.append(f"CLICK, {node['name']}")
                else:
                    rel_x, rel_y = get_relative_coords(node)
                    if rel_x is not None and rel_y is not None:
                        steps.append(f"CLICK_COORDS, {int(rel_x)}, {int(rel_y)}")
                    else:
                        steps.append("CLICK_COORDS, 0, 0")
                steps.append(f"SLEEP, {SLEEP_DURATION}")
                if destination_name and destination_name != "Unknown":
                    steps.append(f"CHECK, {destination_name}")
                testcase = f"{tc_name}, " + ", ".join(steps)
                testcases.append(testcase)

with open("testCase.txt", "w", encoding="utf-8") as f:
    f.write(f"{SDB_TARGET_IP}\n")
    f.write(f"LOOP, {LOOP_COUNT}\n")
    for tc in testcases:
        f.write(tc + "\n")

print(f"✅ {len(testcases)} test cases written to testCase.txt") 