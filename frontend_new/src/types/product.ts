
export interface ChartDataPoint {
  date: string;
  actual: number | null;
  predicted: number | null;
}

export interface Product {
  id: string;
  name: string;
  price: string;
  originalPrice?: string;
  rating: number;
  reviewCount: number;
  image: string;
  store: string;
  discount?: string;
  valueScore: number;
  specs: string[];
  priceChange: number;
  chartData: ChartDataPoint[];
}
