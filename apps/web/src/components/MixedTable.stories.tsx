/** Mixed-content table: Mono numerics next to Sans language content, with
 *  negative values, nulls and long names, on the scrollable table wrapper. */
export const MixedTable = () => (
  <div className="holdings-table-wrap">
    <table className="holdings-table">
      <thead>
        <tr>
          <th scope="col">Symbol</th>
          <th scope="col">Name</th>
          <th scope="col">Target weight</th>
          <th scope="col">Rank</th>
          <th scope="col">Score</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td className="mono-compact">510300</td>
          <td>华泰柏瑞沪深300交易型开放式指数证券投资基金</td>
          <td className="mono-compact">50.00%</td>
          <td className="mono-compact">1</td>
          <td className="mono-compact">0.812345</td>
        </tr>
        <tr>
          <td className="mono-compact">511010</td>
          <td>国债ETF</td>
          <td className="mono-compact">-12.50%</td>
          <td className="mono-compact">—</td>
          <td className="mono-compact">-0.123456</td>
        </tr>
        <tr>
          <td className="mono-compact">159915</td>
          <td>易方达创业板交易型开放式指数证券投资基金</td>
          <td className="mono-compact">—</td>
          <td className="mono-compact">2</td>
          <td className="mono-compact">0.654321</td>
        </tr>
      </tbody>
    </table>
  </div>
);

/** A mixed-content table inside a standard research panel. */
export const TableInPanel = () => (
  <article className="dashboard-panel">
    <div className="panel-heading">
      <h3>Latest signal target holdings</h3>
      <div className="panel-heading-end">
        <span className="panel-heading-eyebrow">Signal</span>
      </div>
    </div>
    <MixedTable />
  </article>
);
