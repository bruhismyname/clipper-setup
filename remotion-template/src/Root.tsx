import "./index.css";
import { MyComposition } from "./Composition";
import { ContentRewardComposition } from "./ContentRewardVideo";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <MyComposition />
      <ContentRewardComposition />
    </>
  );
};
