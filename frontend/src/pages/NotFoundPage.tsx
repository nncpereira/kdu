import { Link } from "react-router-dom";
import { Logo } from "@/components/Logo";
import { Button } from "@/components/Button";

export function NotFoundPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100 p-4">
      <div className="relative w-full max-w-md">
        <div className="bg-white rounded-2xl shadow-2xl overflow-hidden text-center">
          <div className="bg-brand-700 px-8 pt-10 pb-8">
            <div className="inline-flex items-center justify-center w-24 h-24 rounded-full bg-white shadow-inner">
              <Logo size={84} />
            </div>
            <p className="mt-5 text-7xl font-black text-white tracking-tight">
              404
            </p>
            <p className="text-brand-100 text-xs mt-1 uppercase tracking-widest">
              KDU · Cooperative Core
            </p>
          </div>

          <div className="px-8 py-8 space-y-5">
            <div>
              <h1 className="text-xl font-bold text-gray-800">
                Page not found
              </h1>
              <p className="text-sm text-gray-500 mt-2">
                The page you're looking for doesn't exist, or you may not
                have access to it.
              </p>
            </div>

            <Link to="/" className="block">
              <Button className="w-full">Back to KDU</Button>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
