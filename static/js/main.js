document.documentElement.classList.add("js");

const tocLinks = [...document.querySelectorAll(".post-toc a[href^='#']")];
const headings = tocLinks
  .map((link) => document.getElementById(decodeURIComponent(link.hash.slice(1))))
  .filter(Boolean);

if (tocLinks.length && headings.length && "IntersectionObserver" in window) {
  const linksById = new Map(
    tocLinks.map((link) => [decodeURIComponent(link.hash.slice(1)), link]),
  );

  const setActiveLink = (id) => {
    tocLinks.forEach((link) => {
      const isActive = link === linksById.get(id);
      link.classList.toggle("is-active", isActive);
      if (isActive) {
        link.setAttribute("aria-current", "location");
      } else {
        link.removeAttribute("aria-current");
      }
    });
  };

  const observer = new IntersectionObserver(
    (entries) => {
      const visibleHeading = entries
        .filter((entry) => entry.isIntersecting)
        .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)[0];

      if (visibleHeading) {
        setActiveLink(visibleHeading.target.id);
      }
    },
    { rootMargin: "-12% 0px -72% 0px" },
  );

  headings.forEach((heading) => observer.observe(heading));
  setActiveLink(headings[0].id);
}
