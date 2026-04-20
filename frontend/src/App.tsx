import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { PublicLayout } from "@/components/PublicLayout";
import { Home } from "@/pages/public/Home";
import { SearchPage } from "@/pages/public/SearchPage";
import { CategoryProducts } from "@/pages/public/CategoryProducts";
import { ProductDetail } from "@/pages/public/ProductDetail";
import { AdminLayout } from "@/pages/admin/AdminLayout";
import { AdminHome } from "@/pages/admin/AdminHome";
import { AdminCategories } from "@/pages/admin/AdminCategories";
import { AdminParts } from "@/pages/admin/AdminParts";
import { AdminUploads } from "@/pages/admin/AdminUploads";
import { AdminProducts } from "@/pages/admin/AdminProducts";
import { ProductWorkspace } from "@/pages/admin/ProductWorkspace";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<PublicLayout />}>
          <Route path="/" element={<Home />} />
          <Route path="/search" element={<SearchPage />} />
          <Route path="/c/:categorySlug" element={<CategoryProducts />} />
          <Route path="/c/:categorySlug/p/:productSlug" element={<ProductDetail />} />
        </Route>

        <Route path="/admin" element={<AdminLayout />}>
          <Route index element={<AdminHome />} />
          <Route path="categories" element={<AdminCategories />} />
          <Route path="parts" element={<AdminParts />} />
          <Route path="uploads" element={<AdminUploads />} />
          <Route path="products" element={<AdminProducts />} />
          <Route path="products/:productId" element={<ProductWorkspace />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
