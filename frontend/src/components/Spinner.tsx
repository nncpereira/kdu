export function Spinner() {
  return (
    <div className="flex justify-center items-center h-full py-12">
      <div className="w-8 h-8 border-4 border-brand-500 border-t-transparent rounded-full animate-spin" />
    </div>
  );
}