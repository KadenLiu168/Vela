type PaginationProps = {
  offset: number;
  pageSize: number;
  itemCount: number;
  onOffsetChange: (value: number) => void;
};

export function Pagination({ offset, pageSize, itemCount, onOffsetChange }: PaginationProps) {
  const hasPrevious = offset > 0;
  const hasNext = itemCount >= pageSize;

  return (
    <div className="list-pagination">
      <button
        disabled={!hasPrevious}
        onClick={() => onOffsetChange(Math.max(0, offset - pageSize))}
        type="button"
      >
        Previous
      </button>
      <button
        disabled={!hasNext}
        onClick={() => onOffsetChange(offset + pageSize)}
        type="button"
      >
        Next
      </button>
    </div>
  );
}
