// app/dashboard/page.tsx
export default function DataInputPage() {
  return (
<div className="overlay overflow-x-hidden">
  <div className="px-4 py-5 lg:py-8 xl:py-20 mx-auto w-full max-w-screen-xl">
    <h1 className="font-waldenburg-ht text-2xl text-foreground font-semibold mb-5">
      Knowledge Base
    </h1>
    <div className="flex gap-2 mb-4">
      <button
        type="button"
        aria-haspopup="dialog"
        aria-expanded="false"
        aria-controls="radix-:rlb:"
        data-state="closed"
        className="h-20 p-4 pb-3 min-w-32 flex flex-col basis-32 justify-between items-start rounded-xl whitespace-nowrap text-sm font-medium transition-colors duration-200 focus-ring text-foreground border bg-background/20 hover:bg-gray-alpha-50 active:bg-gray-alpha-100"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="24"
          height="24"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="lucide lucide-globe w-4 h-4"
        >
          <circle cx="12" cy="12" r="10"></circle>
          <path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"></path>
          <path d="M2 12h20"></path>
        </svg>
        Add URL
      </button>
      <button
        type="button"
        aria-haspopup="dialog"
        aria-expanded="false"
        aria-controls="radix-:rlg:"
        data-state="closed"
        className="h-20 p-4 pb-3 min-w-32 flex flex-col basis-32 justify-between items-start rounded-xl whitespace-nowrap text-sm font-medium transition-colors duration-200 focus-ring text-foreground border bg-background/20 hover:bg-gray-alpha-50 active:bg-gray-alpha-100"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="24"
          height="24"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="lucide lucide-file-text w-4 h-4"
        >
          <path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"></path>
          <path d="M14 2v4a2 2 0 0 0 2 2h4"></path>
          <path d="M10 9H8"></path>
          <path d="M16 13H8"></path>
          <path d="M16 17H8"></path>
        </svg>
        Add Files
      </button>
      <button
        type="button"
        aria-haspopup="dialog"
        aria-expanded="false"
        aria-controls="radix-:rll:"
        data-state="closed"
        className="h-20 p-4 pb-3 min-w-32 flex flex-col basis-32 justify-between items-start rounded-xl whitespace-nowrap text-sm font-medium transition-colors duration-200 focus-ring text-foreground border bg-background/20 hover:bg-gray-alpha-50 active:bg-gray-alpha-100"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="24"
          height="24"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="lucide lucide-type w-4 h-4"
        >
          <polyline points="4 7 4 4 20 4 20 7"></polyline>
          <line x1="9" x2="15" y1="20" y2="20"></line>
          <line x1="12" x2="12" y1="4" y2="20"></line>
        </svg>
        Create Text
      </button>
    </div>
    {/* Removed the search component */}
    <div className="flex gap-1 mb-2"></div>
    <div className="w-full transition-opacity duration-200 overflow-hidden bleed-x-2 px-2">
      <table className="w-full text-sm border-separate border-spacing-y-2 border-spacing-x-0">
        <thead className="h-9">
          <tr className="group rounded-lg transition-colors">
            <th className="px-2 text-left align-middle font-medium text-subtle border-b">Name</th>
            <th className="px-2 text-left align-middle font-medium text-subtle border-b whitespace-nowrap max-md:hidden">Created by</th>
            <th className="px-2 text-left align-middle font-medium text-subtle border-b whitespace-nowrap max-sm:hidden">Last updated</th>
            <th className="px-2 text-left align-middle font-medium text-subtle border-b w-0">
              <span className="sr-only">Actions</span>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr className="group rounded-lg transition-colors cursor-pointer hover:bg-gray-alpha-50 focus-ring" role="button" >
            <td className="p-2 align-middle first:rounded-l-lg last:rounded-r-lg max-w-[50vw] overflow-hidden">
              <div className="flex gap-2 items-center">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="24"
                  height="24"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="lucide lucide-file-text w-4 h-4 m-0.5 self-start shrink-0"
                >
                  <path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"></path>
                  <path d="M14 2v4a2 2 0 0 0 2 2h4"></path>
                  <path d="M10 9H8"></path>
                  <path d="M16 13H8"></path>
                  <path d="M16 17H8"></path>
                </svg>
                <div className="mr-auto">
                  <p className="text-sm text-foreground font-medium line-clamp-1">Resume_1.3.pdf</p>
                  <p className="text-sm text-subtle font-normal line-clamp-1">3.6 kB</p>
                </div>
              </div>
            </td>
            <td className="p-2 align-middle first:rounded-l-lg last:rounded-r-lg whitespace-nowrap max-md:hidden">
              k23085731@kcl.ac.uk
            </td>
            <td className="p-2 align-middle first:rounded-l-lg last:rounded-r-lg whitespace-nowrap max-sm:hidden">
              <span className="[first-letter:capitalize]">12 Mar, 13:29</span>
            </td>
            <td className="p-2 align-middle first:rounded-l-lg last:rounded-r-lg w-0">
              <button
                aria-label="Document options"
                type="button"
                aria-haspopup="dialog"
                aria-expanded="false"
                aria-controls="radix-:rls:"
                data-state="closed"
                className="relative inline-flex items-center justify-center whitespace-nowrap text-sm font-medium transition-colors duration-200 focus-ring disabled:pointer-events-auto bg-transparent text-foreground hover:bg-gray-alpha-100 active:bg-gray-alpha-200 disabled:bg-transparent disabled:text-gray-400 rounded-[10px] center p-0 h-9 w-9"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="24"
                  height="24"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="lucide lucide-ellipsis w-4 h-4"
                >
                  <circle cx="12" cy="12" r="1"></circle>
                  <circle cx="19" cy="12" r="1"></circle>
                  <circle cx="5" cy="12" r="1"></circle>
                </svg>
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</div>

  );
}
