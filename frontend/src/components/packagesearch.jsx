import { useState } from "react";

function PackageSearch({ onSearch }) {
  const [packageId, setPackageId] = useState("");

  function show() {
    if (packageId === "") {
      return;
    }
    onSearch(packageId);
  }

  return (
    <>
      <h2>Find a package</h2>
      <input value={packageId} onChange={(e) => setPackageId(e.target.value)} placeholder="Package ID" />
      <button onClick={show}>Show</button>
    </>
  );
}

export default PackageSearch;