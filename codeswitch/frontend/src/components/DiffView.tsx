// src/components/DiffView.tsx
// Pure TS line-diff using LCS (no external library)

interface DiffEntry {
  type: 'same' | 'add' | 'remove';
  value: string;
}

interface DiffViewProps {
  before: string;
  after: string;
  height?: string;
}

function lcs(a: string[], b: string[]): DiffEntry[] {
  const m = a.length, n = b.length;
  const dp = Array.from({ length: m + 1 }, () => new Array(n + 1).fill(0) as number[]);
  for (let i = 1; i <= m; i++)
    for (let j = 1; j <= n; j++)
      dp[i][j] = a[i - 1] === b[j - 1] ? dp[i - 1][j - 1] + 1 : Math.max(dp[i - 1][j], dp[i][j - 1]);

  const result: DiffEntry[] = [];
  let i = m, j = n;
  while (i > 0 || j > 0) {
    if (i > 0 && j > 0 && a[i - 1] === b[j - 1]) {
      result.unshift({ type: 'same', value: a[i - 1] });
      i--; j--;
    } else if (j > 0 && (i === 0 || dp[i][j - 1] >= dp[i - 1][j])) {
      result.unshift({ type: 'add', value: b[j - 1] });
      j--;
    } else {
      result.unshift({ type: 'remove', value: a[i - 1] });
      i--;
    }
  }
  return result;
}

export default function DiffView({ before, after, height = '420px' }: DiffViewProps) {
  const beforeLines = (before || '').split('\n');
  const afterLines = (after || '').split('\n');
  const diff = lcs(beforeLines, afterLines);

  return (
    <div className="diff-view" style={{ height, overflowY: 'auto' }}>
      {diff.map((entry, i) => (
        <div key={i} className={`diff-line diff-line-${entry.type}`}>
          <span className="diff-sign">
            {entry.type === 'add' ? '+' : entry.type === 'remove' ? '−' : ' '}
          </span>
          <pre className="diff-text">{entry.value}</pre>
        </div>
      ))}
    </div>
  );
}
