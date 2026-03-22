/** @jsxImportSource https://esm.sh/react@18.2.0 */
import React, {
  useState,
  useEffect,
  useCallback,
  useMemo,
} from "https://esm.sh/react@18.2.0";
import { type Memory } from "../../shared/types.ts";

const API_BASE = "/api/memories";
const MEMORIES_PER_PAGE = 20;

// Format date in natural way: "Wed, April 12"
const formatDate = (dateStr: string) => {
  if (!dateStr) return "N/A";

  // Parse the date parts manually to avoid timezone issues
  const [year, month, day] = dateStr.split("-").map((num) => parseInt(num, 10));

  // Create date with explicit year, month (0-indexed), and day
  const date = new Date(year, month - 1, day);

  return date.toLocaleDateString("en-US", {
    weekday: "short",
    month: "long",
    day: "numeric",
  });
};

// Sort memories by date (ascending)
const sortMemoriesByDate = (memories: Memory[]) => {
  return [...memories].sort((a, b) => {
    if (!a.date) return 1;
    if (!b.date) return -1;

    // Parse dates manually to avoid timezone issues
    const [aYear, aMonth, aDay] = a.date
      .split("-")
      .map((num) => parseInt(num, 10));
    const [bYear, bMonth, bDay] = b.date
      .split("-")
      .map((num) => parseInt(num, 10));

    // Compare year, then month, then day
    if (aYear !== bYear) return aYear - bYear;
    if (aMonth !== bMonth) return aMonth - bMonth;
    return aDay - bDay;
  });
};

interface NotebookViewProps {
  onClose: () => void;
  avatarUrl: string | null;
}

export function NotebookView({ onClose, avatarUrl }: NotebookViewProps) {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editingMemory, setEditingMemory] = useState<Memory | null>(null);
  const [newMemoryText, setNewMemoryText] = useState("");
  const [newMemoryDate, setNewMemoryDate] = useState(
    new Date().toISOString().split("T")[0]
  );
  const [newMemoryTags, setNewMemoryTags] = useState("");
  const [showAddForm, setShowAddForm] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);

  const fetchMemories = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(API_BASE);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setMemories(data);
    } catch (e) {
      console.error("Failed to fetch memories:", e);
      setError(e.message || "Failed to fetch memories.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMemories();
  }, [fetchMemories]);

  const handleAddMemory = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMemoryText.trim()) return;

    const memoryData: Omit<Memory, "id"> = {
      text: newMemoryText,
      date: newMemoryDate,
      tags: newMemoryTags || null,
    };

    try {
      const response = await fetch(API_BASE, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(memoryData),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      setNewMemoryText("");
      setNewMemoryDate(new Date().toISOString().split("T")[0]);
      setNewMemoryTags("");
      setShowAddForm(false);
      await fetchMemories();
    } catch (e) {
      console.error("Failed to add memory:", e);
      setError(e.message || "Failed to add memory.");
    }
  };

  const handleDeleteMemory = async (id: string) => {
    if (!confirm("Are you sure you want to delete this memory?")) return;

    try {
      const response = await fetch(`${API_BASE}/${id}`, {
        method: "DELETE",
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      await fetchMemories();
    } catch (e) {
      console.error("Failed to delete memory:", e);
      setError(e.message || "Failed to delete memory.");
    }
  };

  const handleEditMemory = (memory: Memory) => {
    setEditingMemory(memory);
  };

  const handleCancelEdit = () => {
    setEditingMemory(null);
  };

  const handleUpdateMemory = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingMemory || !editingMemory.text.trim()) return;

    const updatedFields: Partial<Omit<Memory, "id">> = {
      text: editingMemory.text,
      date: editingMemory.date,
      tags: editingMemory.tags,
    };

    try {
      const response = await fetch(`${API_BASE}/${editingMemory.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updatedFields),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      setEditingMemory(null);
      await fetchMemories();
    } catch (e) {
      console.error("Failed to update memory:", e);
      setError(e.message || "Failed to update memory.");
    }
  };

  // Sort and paginate memories
  const sortedMemories = useMemo(
    () => sortMemoriesByDate(memories),
    [memories]
  );

  const totalPages = Math.max(
    1,
    Math.ceil(sortedMemories.length / MEMORIES_PER_PAGE)
  );

  const paginatedMemories = useMemo(() => {
    const startIndex = (currentPage - 1) * MEMORIES_PER_PAGE;
    return sortedMemories.slice(startIndex, startIndex + MEMORIES_PER_PAGE);
  }, [sortedMemories, currentPage]);

  const goToNextPage = () => {
    if (currentPage < totalPages) {
      setCurrentPage(currentPage + 1);
    }
  };

  const goToPrevPage = () => {
    if (currentPage > 1) {
      setCurrentPage(currentPage - 1);
    }
  };

  // Render edit form modal
  const renderEditForm = () => (
    <div className="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center p-4 z-50">
      <form
        onSubmit={handleUpdateMemory}
        className="bg-[#f8f1e0] p-4 rounded-lg shadow-xl w-full max-w-lg border-2 border-[#8B4513]"
      >
        <h2 className="text-2xl font-pixel mb-2 text-[#4b3621]">Edit Entry</h2>
        <div className="mb-2">
          <label
            htmlFor="editText"
            className="block text-lg font-pixel text-[#4b3621] mb-1"
          >
            Text
          </label>
          <textarea
            id="editText"
            value={editingMemory?.text}
            onChange={(e) =>
              setEditingMemory({ ...editingMemory!, text: e.target.value })
            }
            className="w-full p-2 bg-[#fff8dc] border-2 border-[#8B4513] text-[#4b3621] focus:outline-none focus:border-[#654321] font-pixel text-base leading-[1.2em]"
            rows={3}
            required
          />
        </div>
        <div className="mb-2">
          <label
            htmlFor="editDate"
            className="block text-lg font-pixel text-[#4b3621] mb-1"
          >
            Date
          </label>
          <input
            type="date"
            id="editDate"
            value={editingMemory?.date?.split("T")[0] || ""}
            onChange={(e) =>
              setEditingMemory({ ...editingMemory!, date: e.target.value })
            }
            className="w-full p-1 bg-[#fff8dc] border-2 border-[#8B4513] text-[#4b3621] focus:outline-none focus:border-[#654321] font-pixel text-base"
          />
        </div>
        <div className="mb-2">
          <label
            htmlFor="editTags"
            className="block text-lg font-pixel text-[#4b3621] mb-1"
          >
            Source
          </label>
          <input
            type="text"
            id="editTags"
            value={editingMemory?.tags || ""}
            onChange={(e) =>
              setEditingMemory({ ...editingMemory!, tags: e.target.value })
            }
            className="w-full p-1 bg-[#fff8dc] border-2 border-[#8B4513] text-[#4b3621] focus:outline-none focus:border-[#654321] font-pixel text-base"
          />
        </div>
        <div className="flex justify-between mt-3">
          <div className="flex gap-2">
            <button
              type="submit"
              className="px-3 py-1 bg-[#8B4513] text-[#f8f1e0] rounded font-pixel text-base hover:bg-[#654321] border-2 border-b-4 border-r-4 border-[#4b3621]"
            >
              UPDATE
            </button>
            <button
              type="button"
              onClick={() => setEditingMemory(null)}
              className="px-3 py-1 bg-[#A0522D] text-[#f8f1e0] rounded font-pixel text-base hover:bg-[#8B4513] border-2 border-b-4 border-r-4 border-[#4b3621]"
            >
              CANCEL
            </button>
          </div>
          <button
            type="button"
            onClick={() =>
              editingMemory && handleDeleteMemory(editingMemory.id)
            }
            className="px-3 py-1 bg-[#555555] text-white rounded font-pixel text-base hover:bg-[#333333] border-2 border-b-4 border-r-4 border-[#222222]"
          >
            DELETE
          </button>
        </div>
      </form>
    </div>
  );

  // Render add form
  const renderAddForm = () => (
    <div className="add-form mt-3">
      <form
        onSubmit={handleAddMemory}
        className="bg-[#f8f1e0] p-4 rounded-lg border-2 border-[#8B4513] opacity-95 shadow-xl"
      >
        <h2 className="text-2xl font-pixel mb-2 text-[#4b3621]">New Entry</h2>
        <div className="mb-2">
          <textarea
            id="newText"
            value={newMemoryText}
            onChange={(e) => setNewMemoryText(e.target.value)}
            className="w-full p-1 bg-[#fff8dc] border-2 border-[#8B4513] text-[#4b3621] focus:outline-none focus:border-[#654321] font-pixel text-base leading-[1.2em]"
            rows={2}
            placeholder="Enter your note..."
            required
          />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mb-2">
          <div>
            <label
              htmlFor="newDate"
              className="block text-lg font-pixel text-[#4b3621] mb-1"
            >
              Date
            </label>
            <input
              type="date"
              id="newDate"
              value={newMemoryDate}
              onChange={(e) => setNewMemoryDate(e.target.value)}
              className="w-full p-1 bg-[#fff8dc] border-2 border-[#8B4513] text-[#4b3621] focus:outline-none focus:border-[#654321] font-pixel text-base"
            />
          </div>
          <div>
            <label
              htmlFor="newTags"
              className="block text-lg font-pixel text-[#4b3621] mb-1"
            >
              Source
            </label>
            <input
              type="text"
              id="newTags"
              value={newMemoryTags}
              onChange={(e) => setNewMemoryTags(e.target.value)}
              className="w-full p-1 bg-[#fff8dc] border-2 border-[#8B4513] text-[#4b3621] focus:outline-none focus:border-[#654321] font-pixel text-base"
              placeholder="Optional source"
            />
          </div>
        </div>
        <div className="flex gap-2 mt-3">
          <button
            type="submit"
            className="px-3 py-1 bg-[#8B4513] text-[#f8f1e0] rounded font-pixel text-base hover:bg-[#654321] border-2 border-b-4 border-r-4 border-[#4b3621]"
          >
            SAVE
          </button>
          <button
            type="button"
            onClick={() => setShowAddForm(false)}
            className="px-3 py-1 bg-[#A0522D] text-[#f8f1e0] rounded font-pixel text-base hover:bg-[#8B4513] border-2 border-b-4 border-r-4 border-[#4b3621]"
          >
            CANCEL
          </button>
        </div>
      </form>
    </div>
  );

  return (
    <div className="fixed inset-0 bg-black bg-opacity-80 flex flex-col items-center justify-center z-50">
      <div className="relative w-[95vw] max-w-6xl">
        <button
          onClick={onClose}
          className="absolute -top-10 right-0 px-3 py-1 bg-[#8B4513] text-[#f8f1e0] rounded font-pixel text-base hover:bg-[#654321] border-2 border-b-4 border-r-4 border-[#4b3621] z-10"
        >
          CLOSE
        </button>

        <div className="notebook rounded-lg overflow-hidden h-[75vh] flex">
          <div className="notebook-binding w-8 flex-shrink-0"></div>
          <div className="flex-1 p-3 md:p-5 h-full flex flex-col bg-[#A0522D]">
            <div className="flex items-center mb-3">
              <h1 className="text-2xl font-pixel text-[#f8f1e0]">
                Stevens' Notebook
              </h1>
            </div>

            {error && (
              <div
                className="bg-[#A0522D] border-2 border-[#654321] text-[#f8f1e0] px-2 py-1 text-sm rounded mt-2 mb-2 opacity-90 max-w-xl font-pixel"
                role="alert"
              >
                ERROR: {error}
              </div>
            )}

            {loading ? (
              <div className="notebook-pages rounded-lg p-4 flex-1 overflow-auto flex items-center justify-center">
                <p className="text-xl font-pixel text-[#4b3621]">LOADING...</p>
              </div>
            ) : (
              <div className="notebook-pages rounded-lg p-4 flex-1 overflow-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b-2 border-[#8B4513]">
                      <th className="text-left p-1 text-lg font-pixel text-[#4b3621] w-1/4">
                        DATE
                      </th>
                      <th className="text-left p-1 text-lg font-pixel text-[#4b3621]">
                        NOTE
                      </th>
                      <th className="text-left p-1 text-lg font-pixel text-[#4b3621] w-1/6">
                        SOURCE
                      </th>
                      <th className="text-right p-1 text-lg font-pixel text-[#4b3621] w-16">
                        EDIT
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {paginatedMemories.length === 0 ? (
                      <tr>
                        <td colSpan={4} className="text-center p-3">
                          <p className="text-lg font-pixel text-[#4b3621] italic">
                            NO ENTRIES FOUND
                          </p>
                        </td>
                      </tr>
                    ) : (
                      paginatedMemories.map((memory) => (
                        <tr key={memory.id} className="memory-row">
                          <td className="py-1 px-1 align-top">
                            <span className="text-base font-pixel text-[#4b3621] leading-[1.2em] block">
                              {formatDate(memory.date)}
                            </span>
                          </td>
                          <td className="py-1 px-1 align-top">
                            <span
                              className="text-base font-pixel text-[#4b3621] leading-[1.2em] block line-clamp-2"
                              title={memory.text}
                            >
                              {memory.text}
                            </span>
                          </td>
                          <td className="py-1 px-1 align-top">
                            <span
                              className="text-base font-pixel text-[#4b3621] italic leading-[1.2em] block line-clamp-2"
                              title={memory.tags || ""}
                            >
                              {memory.tags || ""}
                            </span>
                          </td>
                          <td className="py-1 px-1 align-top text-right">
                            <button
                              onClick={() => handleEditMemory(memory)}
                              className="mr-1 text-[#8B4513] hover:text-[#654321] font-pixel text-lg"
                              title="Edit"
                            >
                              ✎
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            )}

            <div className="flex justify-between mt-4">
              <div className="flex gap-2">
                <button
                  onClick={goToPrevPage}
                  disabled={currentPage === 1}
                  className={`px-3 py-1 rounded font-pixel text-base border-2 border-b-4 border-r-4
                  ${
                    currentPage === 1
                      ? "bg-[#A0522D] text-[#f8f1e0] opacity-50 cursor-not-allowed"
                      : "bg-[#8B4513] text-[#f8f1e0] hover:bg-[#654321] border-[#4b3621]"
                  }`}
                >
                  PREV
                </button>
                <button
                  onClick={goToNextPage}
                  disabled={currentPage === totalPages}
                  className={`px-3 py-1 rounded font-pixel text-base border-2 border-b-4 border-r-4
                  ${
                    currentPage === totalPages
                      ? "bg-[#A0522D] text-[#f8f1e0] opacity-50 cursor-not-allowed"
                      : "bg-[#8B4513] text-[#f8f1e0] hover:bg-[#654321] border-[#4b3621]"
                  }`}
                >
                  NEXT
                </button>
              </div>
              <div className="text-center font-pixel text-[#f8f1e0] text-sm pt-2">
                Page {currentPage} of {totalPages}
              </div>
            </div>
          </div>
        </div>

        <div className="mt-3 flex justify-center">
          {!showAddForm ? (
            <button
              onClick={() => setShowAddForm(true)}
              className="px-4 py-2 bg-[#8B4513] text-[#f8f1e0] rounded font-pixel text-lg hover:bg-[#654321] shadow-md border-2 border-b-4 border-r-4 border-[#4b3621]"
            >
              NEW ENTRY
            </button>
          ) : (
            <div className="w-full max-w-xl">{renderAddForm()}</div>
          )}
        </div>
      </div>

      {/* Edit Modal */}
      {editingMemory && renderEditForm()}
    </div>
  );
}

