export async function getHealth() {
  const res = await fetch("http://localhost:8000/health/ready");
  return res.json();
}

export async function getGovernor() {
  const res = await fetch("http://localhost:8000/api/governor");
  return res.json();
}
