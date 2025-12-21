import React from "react";

interface LayoutProps {
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  return (
    <div className="min-h-screen bg-black text-white flex">
      <main className="flex-1 p-8 overflow-y-auto min-h-screen">
        <div className="max-w-7xl mx-auto h-full">{children}</div>
      </main>
    </div>
  );
};
