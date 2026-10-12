import "./index.css";
import { MyComposition } from "./Composition";
import { ContentRewardComposition } from "./ContentRewardVideo";
import { FullBleedComposition } from "./FullBleedClip";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <MyComposition />
      <ContentRewardComposition />
      <FullBleedComposition />
    </>
  );
};
