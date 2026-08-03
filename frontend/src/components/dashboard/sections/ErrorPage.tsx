export default function ErrorPage() {
  return (
    <div className="max-w-200 flex flex-col mx-auto size-full">
      <header>
        <img src="/deplocker.png"></img>
      </header>
      <main>
        <div className="text-center py-10 px-4 sm:px-6 lg:px-8">
          <h1 className="block text-7xl font-bold text-primary sm:text-9xl">
            400
          </h1>
          <p className="mt-3 text-muted-foreground">
            Oops, something went wrong.
          </p>
        </div>
      </main>
    </div>
  );
}
