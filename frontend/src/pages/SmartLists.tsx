/**
 * Smart Lists Page Component
 * Main page for managing shopping lists
 */

import React, { useState } from 'react';
import { Plus, ShoppingCart, Users, TrendingDown } from 'lucide-react';
import { useSmartLists } from '../hooks/useSmartLists';
import { SmartList, ListTemplate } from '../types/alerts';
import { ListCard } from '../components/lists/ListCard';
import { ListDetailView } from '../components/lists/ListDetailView';
import { CompareDrawer } from '../components/lists/CompareDrawer';
import { TemplateSelector } from '../components/lists/TemplateSelector';

export const SmartListsPage: React.FC = () => {
  const { lists, templates, loading, createList, deleteList, startComparison } = useSmartLists();
  const [selectedList, setSelectedList] = useState<SmartList | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showTemplates, setShowTemplates] = useState(false);
  const [compareJobId, setCompareJobId] = useState<string | null>(null);
  const [newListName, setNewListName] = useState('');
  const [newListDescription, setNewListDescription] = useState('');
  const [createLoading, setCreateLoading] = useState(false);

  const handleCreateList = async () => {
    if (!newListName.trim()) return;
    
    try {
      setCreateLoading(true);
      await createList({
        name: newListName,
        description: newListDescription,
        is_public: false,
      });
      setShowCreateModal(false);
      setNewListName('');
      setNewListDescription('');
    } catch (err) {
      console.error('Failed to create list:', err);
    } finally {
      setCreateLoading(false);
    }
  };

  const handleDeleteList = async (id: number) => {
    if (!confirm('Are you sure you want to delete this list?')) return;
    try {
      await deleteList(id);
      if (selectedList?.id === id) {
        setSelectedList(null);
      }
    } catch (err) {
      console.error('Failed to delete list:', err);
    }
  };

  const handleStartCompare = async (listId: number) => {
    try {
      const result = await startComparison(listId);
      setCompareJobId(result.job_id);
    } catch (err) {
      console.error('Failed to start comparison:', err);
    }
  };

  const totalItems = lists.reduce((sum, list) => sum + list.item_count, 0);
  const publicLists = lists.filter(list => list.is_public).length;

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Smart Lists</h1>
            <p className="text-gray-600 mt-1">Organize and compare your shopping lists</p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => setShowTemplates(true)}
              className="px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors flex items-center gap-2"
            >
              <ShoppingCart className="h-5 w-5" />
              Templates
            </button>
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
            >
              <Plus className="h-5 w-5" />
              New List
            </button>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Lists</p>
                <p className="text-2xl font-bold text-gray-900">{lists.length}</p>
              </div>
              <ShoppingCart className="h-8 w-8 text-blue-600" />
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Items</p>
                <p className="text-2xl font-bold text-gray-900">{totalItems}</p>
              </div>
              <TrendingDown className="h-8 w-8 text-green-600" />
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Shared Lists</p>
                <p className="text-2xl font-bold text-gray-900">{publicLists}</p>
              </div>
              <Users className="h-8 w-8 text-purple-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto">
        {selectedList ? (
          <ListDetailView
            list={selectedList}
            onBack={() => setSelectedList(null)}
            onDelete={() => handleDeleteList(selectedList.id)}
            onCompare={() => handleStartCompare(selectedList.id)}
          />
        ) : (
          <>
            {loading ? (
              <div className="flex justify-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
              </div>
            ) : lists.length === 0 ? (
              <div className="text-center py-12 bg-white rounded-lg shadow">
                <ShoppingCart className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No lists yet</h3>
                <p className="text-gray-600 mb-4">Create your first shopping list to get started</p>
                <button
                  onClick={() => setShowCreateModal(true)}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Create List
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {lists.map((list) => (
                  <ListCard
                    key={list.id}
                    list={list}
                    onView={() => setSelectedList(list)}
                    onDelete={() => handleDeleteList(list.id)}
                    onCompare={() => handleStartCompare(list.id)}
                  />
                ))}
              </div>
            )}
          </>
        )}
      </div>

      {/* Create List Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen px-4">
            <div className="fixed inset-0 bg-black opacity-30" onClick={() => setShowCreateModal(false)}></div>
            
            <div className="relative bg-white rounded-lg shadow-xl max-w-md w-full p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Create New List</h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    List Name *
                  </label>
                  <input
                    type="text"
                    value={newListName}
                    onChange={(e) => setNewListName(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="My Shopping List"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Description (Optional)
                  </label>
                  <textarea
                    value={newListDescription}
                    onChange={(e) => setNewListDescription(e.target.value)}
                    rows={3}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Add a description..."
                  />
                </div>
              </div>
              
              <div className="flex gap-3 mt-6">
                <button
                  onClick={() => setShowCreateModal(false)}
                  disabled={createLoading}
                  className="flex-1 px-6 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateList}
                  disabled={createLoading || !newListName.trim()}
                  className="flex-1 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
                >
                  {createLoading ? 'Creating...' : 'Create'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Template Selector Modal */}
      {showTemplates && (
        <TemplateSelector
          templates={templates}
          onClose={() => setShowTemplates(false)}
          onSelect={(template: ListTemplate) => {
            // Create list from template
            createList({
              name: template.name,
              description: template.description,
            }).then(() => setShowTemplates(false));
          }}
        />
      )}

      {/* Compare Drawer */}
      {compareJobId && (
        <CompareDrawer
          jobId={compareJobId}
          onClose={() => setCompareJobId(null)}
        />
      )}
    </div>
  );
};
