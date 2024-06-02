import clang.cindex
import os
import graphviz

clang_dll_path = "C:\\msys64\\mingw64\\bin\\libclang.dll"
source_directory = "D:\\WorkSpace\\nexus-bots-tiva\\firmware"
dot_file_name = "func_tree.dot"
output_file = "func_tree"

# Set clang configuration
clang.cindex.Config.set_library_file(clang_dll_path)

def parse_file(filename):
    index = clang.cindex.Index.create()
    translation_unit = index.parse(filename)
    return translation_unit

def visit_node(node, call_graph, parent=None, source_root=None):
    if node.kind == clang.cindex.CursorKind.FUNCTION_DECL:
        # Kiểm tra xem hàm có được định nghĩa trong thư mục nguồn không
        if node.location.file and source_root in node.location.file.name:
            # Thêm node vào đồ thị
            if node.spelling not in call_graph:
                call_graph[node.spelling] = []
            if parent is not None:
                call_graph[parent].append(node.spelling)
            # Duyệt con của node hiện tại
            for child in node.get_children():
                visit_node(child, call_graph, node.spelling, source_root)
    elif node.kind == clang.cindex.CursorKind.CALL_EXPR:
        # Thêm lời gọi hàm vào đồ thị
        if node.spelling not in call_graph:
            call_graph[node.spelling] = []
        if parent is not None:
            call_graph[parent].append(node.spelling)
        # Duyệt con của node hiện tại
        for child in node.get_children():
            visit_node(child, call_graph, parent, source_root)
    else:
        # Duyệt con của node hiện tại
        for child in node.get_children():
            visit_node(child, call_graph, parent, source_root)

# Hàm để duyệt toàn bộ thư mục và phân tích các tệp .c
def parse_directory(directory, args=[]):
    call_graph = {}
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.cpp'):
                filepath = os.path.join(root, file)
                try:
                    tu = parse_file(filepath)
                    visit_node(tu.cursor, call_graph, source_root=directory)
                except clang.cindex.TranslationUnitLoadError as e:
                    print(f"Error parsing {filepath}: {e}")
    
    return call_graph

# Hàm để loại bỏ các hàm không được gọi bởi các hàm khác
def filter_unused_functions(call_graph):
    used_functions = set()
    
    # Duyệt qua các hàm và kiểm tra xem chúng có được gọi hay không
    for caller, callees in call_graph.items():
        for callee in callees:
            used_functions.add(callee)
    
    # Loại bỏ các hàm không được gọi
    filtered_graph = {func: callees for func, callees in call_graph.items() if func in used_functions or len(callees) > 0}
    
    return filtered_graph

# Hàm để tạo file .dot
def create_dot_file(graph, output_file=dot_file_name):
    with open(output_file, 'w') as f:
        f.write('digraph CallGraph {\n')
        for caller, callees in graph.items():
            for callee in callees:
                f.write(f'  "{caller}" -> "{callee}";\n')
        f.write('}\n')

# Hàm để vẽ đồ thị sử dụng Graphviz
def draw_graph(call_graph, output_file=output_file):
    graph = graphviz.Digraph(comment='Call Graph')
    
    for func, callees in call_graph.items():
        graph.node(func)
        for callee in callees:
            graph.edge(func, callee)
    
    graph.render(output_file, format='png', view=True)

if __name__ == "__main__":
    func_graph = parse_directory(source_directory)

    filtered_graph = filter_unused_functions(func_graph)

    # Vẽ đồ thị
    draw_graph(filtered_graph)

    # Tạo file .dot
    create_dot_file(filtered_graph)
