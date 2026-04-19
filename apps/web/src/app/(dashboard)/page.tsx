export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
        <StatCard label="Allenamenti questa settimana" value="—" />
        <StatCard label="Kcal bruciate (totale)" value="—" />
        <StatCard label="Ore di allenamento" value="—" />
      </div>
      <p className="text-sm text-gray-500">Dashboard in costruzione — i dati appariranno qui.</p>
    </div>
  )
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl bg-white p-6 shadow-sm">
      <p className="text-sm text-gray-500">{label}</p>
      <p className="mt-1 text-3xl font-bold text-brand-700">{value}</p>
    </div>
  )
}
