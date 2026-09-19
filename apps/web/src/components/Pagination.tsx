type PaginationProps = {
  offset: number;
  pageSize: number;
  itemCount: number;
  totalCount?: number;
  onOffsetChange: (value: number) => void;
};

export function Pagination({ offset, pageSize, itemCount, totalCount, onOffsetChange }: PaginationProps) {
  const hasPrevious = offset > 0;
  const hasNext = totalCount === undefined ? itemCount >= pageSize : offset + itemCount < totalCount;

  return (
    <nav aria-label="Pagination" className="list-pagination">
      <button
        className="button-secondary"
        disabled={!hasPrevious}
        onClick={() => onOffsetChange(Math.max(0, offset - pageSize))}
        type="button"
      >
        Previous
      </button>
      <button
        className="button-secondary"
        disabled={!hasNext}
        onClick={() => onOffsetChange(offset + pageSize)}
        type="button"
      >
        Next
      </button>
      <p className="list-pagination-position" role="status">
        {describePosition(offset, itemCount, totalCount)}
      </p>
    </nav>
  );
}

/** A page is only meaningful in relation to the rest of the list, so the
 *  controls state which rows are on screen rather than leaving the user to
 *  infer it from a bare Previous / Next pair. */
function describePosition(offset: number, itemCount: number, totalCount: number | undefined): string {
  if (itemCount === 0) {
    return "No rows at this offset.";
  }

  const first = offset + 1;
  const last = offset + itemCount;

  return totalCount === undefined
    ? `Showing ${first}–${last}.`
    : `Showing ${first}–${last} of ${totalCount}.`;
}
