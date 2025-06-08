
# Enhanced search_by_text method with deduplication
async def search_by_text(self, query_text: str, top_k: int = 10) -> List[Dict]:
    """Search for products using text query with deduplication"""
    try:
        if self.text_index is None or self.text_index.ntotal == 0:
            return []
        
        # Encode query text
        query_embedding = await self.encode_text(query_text)
        
        # Search with larger result set to account for duplicates
        search_k = min(top_k * 3, self.text_index.ntotal)
        scores, indices = self.text_index.search(
            query_embedding.reshape(1, -1), search_k
        )
        
        # Deduplicate by product_id and keep highest scoring entry
        seen_products = {}
        for score, idx in zip(scores[0], indices[0]):
            if idx in self.product_metadata:
                result = self.product_metadata[idx].copy()
                result['similarity_score'] = float(score)
                product_id = result['product_id']
                
                # Keep only the highest scoring entry for each product
                if product_id not in seen_products or result['similarity_score'] > seen_products[product_id]['similarity_score']:
                    seen_products[product_id] = result
        
        # Return top_k unique results sorted by score
        unique_results = list(seen_products.values())
        unique_results.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        return unique_results[:top_k]
        
    except Exception as e:
        logger.error(f"Text search failed: {e}")
        raise
