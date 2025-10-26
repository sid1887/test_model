/**
 * Template Selector Component
 * Browse and select list templates
 */

import React, { useState } from 'react';
import { X, ShoppingCart, Check } from 'lucide-react';
import { ListTemplate } from '../../types/alerts';

interface TemplateSelectorProps {
  templates: ListTemplate[];
  onClose: () => void;
  onSelect: (template: ListTemplate) => void;
}

export const TemplateSelector: React.FC<TemplateSelectorProps> = ({
  templates,
  onClose,
  onSelect,
}) => {
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  // Get unique categories
  const categories = ['all', ...new Set(templates.map(t => t.category))];

  // Filter templates by category
  const filteredTemplates = selectedCategory === 'all'
    ? templates
    : templates.filter(t => t.category === selectedCategory);

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4">
        <div className="fixed inset-0 bg-black opacity-30" onClick={onClose}></div>
        
        <div className="relative bg-white rounded-lg shadow-xl max-w-4xl w-full p-6 max-h-[80vh] overflow-y-auto">
          {/* Header */}
          <div className="flex items-center justify-between mb-6 sticky top-0 bg-white pb-4 border-b border-gray-200">
            <div className="flex items-center gap-3">
              <ShoppingCart className="h-6 w-6 text-blue-600" />
              <h2 className="text-2xl font-bold text-gray-900">List Templates</h2>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <X className="h-6 w-6" />
            </button>
          </div>

          {/* Category Filter */}
          <div className="mb-6">
            <div className="flex gap-2 flex-wrap">
              {categories.map((category) => (
                <button
                  key={category}
                  onClick={() => setSelectedCategory(category)}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors capitalize ${
                    selectedCategory === category
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {category}
                </button>
              ))}
            </div>
          </div>

          {/* Templates Grid */}
          {filteredTemplates.length === 0 ? (
            <div className="text-center py-12">
              <ShoppingCart className="h-16 w-16 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">No templates found in this category</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {filteredTemplates.map((template) => (
                <div
                  key={template.id}
                  className="bg-gray-50 rounded-lg p-4 hover:bg-gray-100 transition-colors cursor-pointer border border-gray-200"
                  onClick={() => onSelect(template)}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-gray-900 mb-1">
                        {template.name}
                      </h3>
                      <span className="inline-block px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full capitalize">
                        {template.category}
                      </span>
                    </div>
                    <Check className="h-5 w-5 text-gray-400" />
                  </div>
                  
                  {template.description && (
                    <p className="text-sm text-gray-600 mb-3">{template.description}</p>
                  )}
                  
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">
                      {template.template_items.length || 0} items
                    </span>
                    {template.is_featured && (
                      <span className="px-2 py-1 bg-yellow-100 text-yellow-700 text-xs rounded-full">
                        Featured
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Close Button */}
          <div className="mt-6 pt-4 border-t border-gray-200">
            <button
              onClick={onClose}
              className="w-full px-6 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
