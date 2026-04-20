export type CategorySummary = {
  id: string;
  slug: string;
  name: string;
  sort_order: number;
  published_product_count: number;
};

export type ProductSummary = {
  id: string;
  slug: string;
  name: string;
  subtitle: string | null;
};

export type HotspotPublic = {
  part_id: string;
  geometry: Record<string, unknown>;
  z_order: number;
  label_anchor: Record<string, unknown> | null;
  public_code: string;
  public_description: string;
  is_orderable: boolean;
};

export type BomLinePublic = {
  part_id: string;
  quantity: number;
  sort_order: number;
  bom_group: string | null;
  show_on_diagram: boolean;
  public_code: string;
  public_description: string;
  is_orderable: boolean;
  part_image_asset_url_path: string | null;
};

export type DiagramPublic = {
  svg_storage_key: string;
  raster_fallback_storage_key: string | null;
  diagram_title: string | null;
  alt_summary: string | null;
};

export type ProductPublishedDetail = {
  category: { slug: string; name: string };
  product: ProductSummary;
  snapshot: { version: number; published_at: string };
  diagram: DiagramPublic | null;
  bill_of_materials: BomLinePublic[];
  diagram_hotspots: HotspotPublic[];
};

export type SearchHit = {
  category_slug: string;
  category_name: string;
  product_id: string;
  product_slug: string;
  product_name: string;
  subtitle: string | null;
};

export type SearchResponse = {
  query: string;
  total: number;
  results: SearchHit[];
};

export type CreateCategoryResponse = {
  id: string;
  slug: string;
  name: string;
  sort_order: number;
};

export type PartListItem = {
  id: string;
  internal_part_number: string;
  internal_description: string | null;
  status: string;
  image_uploaded_asset_id: string | null;
};

export type ProductListItem = {
  id: string;
  category_id: string;
  category_slug: string;
  slug: string;
  name: string;
  subtitle: string | null;
  status: string;
};

export type UploadAssetResponse = {
  id: string;
  storage_key: string;
  kind: string;
  original_filename: string;
  content_type: string;
  byte_size: number;
};

export type ProductDraftDocument = {
  product_id: string;
  payload: Record<string, unknown>;
  updated_at: string | null;
  updated_by_user_id: string | null;
};
