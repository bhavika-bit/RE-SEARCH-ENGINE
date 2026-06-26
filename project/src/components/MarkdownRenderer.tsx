import { useMemo } from 'react';

interface MarkdownRendererProps {
  content: string;
}

export default function MarkdownRenderer({ content }: MarkdownRendererProps) {
  const html = useMemo(() => {
    let result = content;

    // Headers
    result = result.replace(/^### (.*$)/gim, '<h3 class="text-lg font-semibold text-stone-800 dark:text-stone-200 mt-4 mb-2">$1</h3>');
    result = result.replace(/^## (.*$)/gim, '<h2 class="text-xl font-semibold text-stone-800 dark:text-stone-200 mt-6 mb-3">$1</h2>');
    result = result.replace(/^# (.*$)/gim, '<h1 class="text-2xl font-bold text-stone-800 dark:text-stone-200 mt-6 mb-4">$1</h1>');

    // Bold and italic
    result = result.replace(/\*\*\*(.*?)\*\*\*/g, '<strong><em>$1</em></strong>');
    result = result.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-stone-800 dark:text-stone-200">$1</strong>');
    result = result.replace(/\*(.*?)\*/g, '<em>$1</em>');

    // Code blocks
    result = result.replace(/```(\w*)\n([\s\S]*?)```/g, '<pre class="bg-stone-100 dark:bg-stone-900 rounded-lg p-4 overflow-x-auto my-3 text-sm"><code class="text-stone-700 dark:text-stone-300">$2</code></pre>');

    // Inline code
    result = result.replace(/`([^`]+)`/g, '<code class="bg-stone-100 dark:bg-stone-900 px-1.5 py-0.5 rounded text-sm text-amber-600 dark:text-amber-400">$1</code>');

    // Lists
    result = result.replace(/^- (.*$)/gim, '<li class="ml-4 list-disc text-stone-700 dark:text-stone-300 my-1">$1</li>');
    result = result.replace(/^\d+\. (.*$)/gim, '<li class="ml-4 list-decimal text-stone-700 dark:text-stone-300 my-1">$1</li>');

    // Tables
    const tableRegex = /\|(.+)\|\n\|[-\s|:]+\|\n((?:\|.+\|\n?)+)/g;
    result = result.replace(tableRegex, (_, header, body) => {
      const headers = header.split('|').filter((h: string) => h.trim());
      const rows = body.trim().split('\n');

      let tableHtml = '<div class="overflow-x-auto my-4"><table class="min-w-full border-collapse border border-stone-200 dark:border-stone-700 rounded-lg">';
      tableHtml += '<thead class="bg-stone-50 dark:bg-stone-800"><tr>';
      headers.forEach((h: string) => {
        tableHtml += `<th class="border border-stone-200 dark:border-stone-700 px-4 py-2 text-left text-sm font-medium text-stone-700 dark:text-stone-300">${h.trim()}</th>`;
      });
      tableHtml += '</tr></thead><tbody>';

      rows.forEach((row: string) => {
        const cells = row.split('|').filter((c: string) => c.trim());
        tableHtml += '<tr class="bg-white dark:bg-stone-800/50">';
        cells.forEach((cell: string) => {
          tableHtml += `<td class="border border-stone-200 dark:border-stone-700 px-4 py-2 text-sm text-stone-700 dark:text-stone-300">${cell.trim()}</td>`;
        });
        tableHtml += '</tr>';
      });

      tableHtml += '</tbody></table></div>';
      return tableHtml;
    });

    // Paragraphs
    result = result.replace(/\n\n/g, '</p><p class="my-3 text-stone-700 dark:text-stone-300">');
    result = `<p class="my-3 text-stone-700 dark:text-stone-300">${result}</p>`;

    return result;
  }, [content]);

  return (
    <div
      className="markdown-content prose dark:prose-invert max-w-none"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
