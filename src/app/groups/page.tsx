import GroupTable from "@/components/GroupTable";
import { getGroups, getProbabilities, getResults } from "@/lib/data";
import { getPredictionFor } from "@/lib/predictions";

export default function GroupsPage() {
  const groups = getGroups().groups;
  const probabilities = getProbabilities().teams;
  const allMatches = getResults().matches.map((match, index) => ({ match, index }));
  const letters = Object.keys(groups).sort();

  return (
    <div className="flex flex-col gap-10">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Group stage</h1>
        <nav className="mt-2 flex flex-wrap gap-2 text-sm">
          {letters.map((letter) => (
            <a key={letter} href={`#group-${letter}`} className="rounded-sm border border-neutral-200 px-2 py-0.5 hover:border-neutral-400">
              {letter}
            </a>
          ))}
        </nav>
      </div>
      {letters.map((letter) => {
        const fixtures = allMatches
          .filter(({ match }) => match.group === letter)
          .map(({ match, index }) => ({ match, index, prediction: getPredictionFor(match) }));
        return (
          <GroupTable key={letter} letter={letter} standings={groups[letter]} probabilities={probabilities} fixtures={fixtures} />
        );
      })}
    </div>
  );
}
