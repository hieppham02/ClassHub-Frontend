<script setup>
defineProps({ value: { type: Object, default: null } })
const labels = { UNCONFIGURED: 'Chưa gắn đủ thẻ RFID cho danh sách thiết bị.', NO_DATA: 'Chờ dữ liệu quét từ tủ.',
  INCOMPLETE: 'Còn thẻ chưa quét trong lượt này.', WRONG: 'Có thẻ không thuộc danh sách của lượt này.', MATCH: 'Đã quét đủ thẻ theo danh sách.' }
</script>
<template>
  <section class="space-y-2 rounded-lg border border-blue-100 bg-slate-50 p-3 text-sm" aria-live="polite">
    <p class="font-medium">RFID · {{ labels[value?.status] || 'Chờ dữ liệu quét từ tủ.' }}</p>
    <p class="text-xs text-slate-500">Quét từng thẻ một trong lúc cửa đang mở. Lượt quét là bằng chứng xuất trình, chưa chứng minh đồ đã được đặt trong hộc.</p>
    <ul v-if="value?.items?.length" class="space-y-1">
      <li v-for="item in value.items" :key="item.snapshotId">
        {{ item.name }}: đã quét {{ item.scanned }}/{{ item.quantity }} · đã gắn {{ item.assigned }}/{{ item.quantity }} thẻ
        <span v-if="item.missing?.length" class="block break-all text-xs text-amber-700">Chưa quét: {{ item.missing.join(', ') }}</span>
      </li>
    </ul>
    <p v-if="value?.unexpected?.length" class="break-all text-red-700">Thẻ ngoài danh sách: {{ value.unexpected.join(', ') }}</p>
  </section>
</template>
