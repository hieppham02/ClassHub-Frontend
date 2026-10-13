from pathlib import Path
p = Path('src/views/admin/AssetsView.vue')
s = p.read_text(encoding='utf-8')
s = s.replace('<span>Màu demo cho dữ liệu mock; chưa áp dụng ngưỡng thực tế.</span>', '')
s = s.replace('{{ node.name }}', '{{ nodeDisplayName(node) }}')
s = s.replace("{{ node.nodeCode }} · {{ node.dataSource === 'MOCK' ? 'Dữ liệu mock' : 'Dữ liệu node thực tế' }}", '{{ nodeDisplayCode(node) }}')
s = s.replace('{{ n.nodeCode }}', '{{ nodeDisplayCode(n) }}')
s = '\n'.join(line for line in s.split('\n') if not ('<p v-if=' in line and 'Dữ liệu mock lưu sẵn' in line))
p.write_text(s, encoding='utf-8')
p = Path('src/components/admin/layout/AdminSidebar.vue')
s = p.read_text(encoding='utf-8')
start = s.index("  {\n    label: 'Trang người dùng'")
end = s.index("\n  {\n    label: 'Quản lý tài sản'", start)
user = s[start:end].rstrip().removesuffix(',')
s = s[:start] + s[end+1:]
end = s.index('\n]\n', start)
s = s[:end].rstrip() + ',\n' + user + s[end:]
s = s.replace('menuItems[7], // Quản lý tài sản', 'menuItems[6], // Quản lý tài sản').replace('menuItems[6]  // Trang người dùng', 'menuItems[7]  // Trang người dùng')
p.write_text(s, encoding='utf-8')
