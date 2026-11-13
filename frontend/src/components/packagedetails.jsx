function PackageDetails({ pkg }) {
  if (pkg === null) {
    return null;
  }

  return (
    <>
      <h2>Package details</h2>
      <p><strong>ID:</strong> {pkg.id}</p>
      <p><strong>Name:</strong> {pkg.name}</p>
      <p><strong>Destination:</strong> {pkg.destination}</p>
      <p><strong>Weight:</strong> {pkg.weight} kg</p>
      <p><strong>Arrival date:</strong> {pkg.arrival_date}</p>
      <p><strong>Status:</strong> {pkg.status}</p>
    </>
  );
}

export default PackageDetails;