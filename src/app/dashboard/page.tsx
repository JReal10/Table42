// app/dashboard/page.tsx
export default function DashboardPage() {
  return (
    <div className="hstack justify-center p-4 md:p-5 lg:p-12 pt-5 md:pt-8 lg:pt-20 2xl:pt-28">
      <div className = "max-w-5xl w-full">
        <div className = "pb-4 md:pb-8">
          <div className="max-w-full w-max flex items-center text-sm font-medium gap-1 border border-gray-alpha-200 p-1.5 pr-3.5 rounded-full">
            <div className="relative bg-foreground rounded-full h-2 w-2 m-2">
              <div className="absolute inset-0 rounded-full bg-gray-alpha-300"></div>
            </div>
            <span>active calls</span>
            <div className="transform: none; transform-origin: 50% 50% 0px;">
              0
            </div>
          </div>
        </div>
        <div className = "stack flex-wrap gap-4 items-center mb-4 md:mb-6">
        <div className="hstack">
          <div className="text-start overflow-hidden">
            <div><p aria-hidden="true" className="truncate inter font-medium text-sm text-gray-alpha-500 min-h-[20px]">My Workspace </p>
            <h5 aria-hidden="true" className="font-waldenburg-ht font-medium line-clamp-1 text-2xl md:text-3xl text-gray-alpha-950 min-h-[30px]">Good morning</h5>
            </div></div></div>
          </div>

          <div className="stack gap-4 mb-10">
            <div className="eleven-carousel w-full overflow-auto scroll-smooth flex snap-x snap-mandatory no-scrollbar -my-2 py-2 px-2 bleed-x-2">
              <div role="radiogroup" aria-required="false" dir="ltr" className="grid gap-3 grid-cols-4 w-full min-w-max">
                <button type="button" role="radio" aria-checked="true" data-state="checked" value="count" className="relative px-4 py-4 rounded-2xl border text-primary text-start focus-ring hover:bg-gray-alpha-50 hover:shadow disabled:cursor-not-allowed data-[state=&quot;checked&quot;]:bg-gray-alpha-50 disabled:opacity-50 transition-colors duration-200 min-w-max pr-8 scroll-mx-8" data-radix-collection-item="">
                  <p className="text-sm text-subtle font-medium">Number of calls</p>
                  <h5 aria-hidden="true" className="font-waldenburg-ht font-medium line-clamp-1 text-2xl md:text-3xl text-foreground relative">
                    <div className="">0</div>
                  </h5>
                    <span data-state="checked" className="absolute right-2 top-2 border rounded-full">
                      </span></button>
                      <button type="button" role="radio" aria-checked="false" data-state="unchecked" value="average_duration" className="relative px-4 py-4 rounded-2xl border text-primary text-start focus-ring hover:bg-gray-alpha-50 hover:shadow disabled:cursor-not-allowed data-[state=&quot;checked&quot;]:bg-gray-alpha-50 disabled:opacity-50 transition-colors duration-200 min-w-max pr-8 scroll-mx-8" data-radix-collection-item="">
                        <p className="text-sm text-subtle font-medium">Average duration</p>
                        <h5 aria-hidden="true" className="font-waldenburg-ht font-medium line-clamp-1 text-2xl md:text-3xl text-foreground relative">
                          <div className="">0</div></h5></button>
                          <button type="button" role="radio" aria-checked="false" data-state="unchecked" value="cost" className="relative px-4 py-4 rounded-2xl border text-primary text-start focus-ring hover:bg-gray-alpha-50 hover:shadow disabled:cursor-not-allowed data-[state=&quot;checked&quot;]:bg-gray-alpha-50 disabled:opacity-50 transition-colors duration-200 min-w-max pr-8 scroll-mx-8"  data-radix-collection-item=""><p className="text-sm text-subtle font-medium">Total cost</p><h5 aria-hidden="true" className="font-waldenburg-ht font-medium line-clamp-1 text-2xl md:text-3xl text-foreground relative"><div className="">0<span className="text-sm font-normal"> credits</span></div></h5></button><button type="button" role="radio" aria-checked="false" data-state="unchecked" value="average_cost" className="relative px-4 py-4 rounded-2xl border text-primary text-start focus-ring hover:bg-gray-alpha-50 hover:shadow disabled:cursor-not-allowed data-[state=&quot;checked&quot;]:bg-gray-alpha-50 disabled:opacity-50 transition-colors duration-200 min-w-max pr-8 scroll-mx-8" data-radix-collection-item=""><p className="text-sm text-subtle font-medium">Average cost</p><h5 aria-hidden="true" className="font-waldenburg-ht font-medium line-clamp-1 text-2xl md:text-3xl text-foreground relative"><div className="">0<span className="text-sm font-normal"> credits/call</span></div></h5></button></div></div>
          </div>
      </div>
    </div>
  );
}

/* 
      <div className="hstack"><div className="text-start overflow-hidden"><div><p aria-hidden="true" className="truncate inter font-medium text-sm text-gray-alpha-500 min-h-[20px]">My Workspace </p><h5 aria-hidden="true" className="font-waldenburg-ht font-medium line-clamp-1 text-2xl md:text-3xl text-gray-alpha-950 min-h-[30px]">Good morning</h5></div></div></div><div className="flex gap-2 ml-auto"><button type="button" role="combobox" aria-controls="radix-:r2ut:" aria-expanded="false" aria-autocomplete="none" dir="ltr" data-state="closed" className="flex h-9 gap-0.5 items-center justify-between whitespace-nowrap rounded-[10px] border border-gray-alpha-200 bg-transparent pl-3 pr-2 py-2 text-sm shadow-none placeholder:text-muted-foreground focus-ring disabled:cursor-not-allowed disabled:opacity-50 [&amp;>span]:line-clamp-1 w-auto"><span translate="no">All agents</span><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" className="lucide lucide-chevron-down h-4 w-4 opacity-50 min-w-fit ms-1" aria-hidden="true"><path d="m6 9 6 6 6-6"></path></svg></button><button type="button" role="combobox" aria-controls="radix-:r2v0:" aria-expanded="false" aria-autocomplete="none" dir="ltr" data-state="closed" className="flex h-9 gap-0.5 items-center justify-between whitespace-nowrap rounded-[10px] border border-gray-alpha-200 bg-transparent pl-3 pr-2 py-2 text-sm shadow-none placeholder:text-muted-foreground focus-ring disabled:cursor-not-allowed disabled:opacity-50 [&amp;>span]:line-clamp-1 w-auto"><span translate="no">Last month</span><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" className="lucide lucide-chevron-down h-4 w-4 opacity-50 min-w-fit ms-1" aria-hidden="true"><path d="m6 9 6 6 6-6"></path></svg></button></div>!--> */